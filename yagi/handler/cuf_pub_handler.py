import os
import time
import logging
import uuid
from yagi import stats
import yagi
from yagi.config import config
from yagi.handler.http_connection import HttpConnection, InvalidContentException
from yagi.handler.http_connection import MessageDeliveryFailed
from yagi.handler.http_connection import UnauthorizedException
from yagi.handler.notification import Notification, GlanceNotification
import yagi.serializer.cuf

with yagi.config.defaults_for("cufpub") as default:
    default("validate_ssl", "False")
    default("generate_entity_links", "False")
    default("retries", "-1")
    default("url", "http://127.0.0.1/nova")
    default("max_wait", "600")
    default("failures_before_reauth", "5")
    default("interval", "30")
    default("timeout", "120")

LOG = logging.getLogger(__name__)

class CufPub(yagi.handler.BaseHandler):
    CONFIG_SECTION = "cufpub"
    AUTO_ACK = True

    def unescape_strings(self, payload_body):
        return str.replace(str.replace(payload_body, "&lt;", "<"), "&gt;", ">")

    def nova_cuf(self, deployment_info, payload):
        notification = Notification(payload)
        cuf = notification.convert_to_verified_message_in_cuf_format(
            {'region': deployment_info['REGION'],
             'data_center': deployment_info['DATACENTER']})
        entity = dict(content=cuf,
                      id=str(uuid.uuid4()),
                      event_type='compute.instance.exists.verified.cuf',
                      original_message_id=notification.get_original_message_id())
        payload_body = yagi.serializer.cuf.dump_item(entity)
        return self.unescape_strings(payload_body)


    def glance_cuf(self, deployment_info, payload):
        glance_notification = GlanceNotification(payload)
        cuf = glance_notification.convert_to_verified_message_in_cuf_format(
            {'region': deployment_info['DATACENTER'],
             'data_center': deployment_info['REGION']})

        entity = dict(content=cuf,
                      id=str(uuid.uuid4()),
                      event_type='image.exists.verified.cuf',
                      original_message_id=glance_notification.get_original_message_id())
        payload_body = yagi.serializer.cuf.dump_item(entity, service_title="Glance")
        return self.unescape_strings(payload_body)

    def get_deployment_info(self, deployment_info_string):
        data_center = deployment_info_string.split(',')[0].split('=')[1]
        region = deployment_info_string.split(',')[1].split('=')[1]
        deployment_info = {'DATACENTER': data_center, 'REGION': region}
        return deployment_info

    def handle_messages(self, messages,env):
        retries = int(self.config_get("retries"))
        interval = int(self.config_get("interval"))
        max_wait = int(self.config_get("max_wait"))
        failures_before_reauth = int(self.config_get("failures_before_reauth"))
        connection = HttpConnection(self)
        results = env.setdefault('cufpub.results', dict())

        for payload in self.iterate_payloads(messages, env):
            msgid = payload["message_id"]
            try:
                deployment_info_string = yagi.config.get('event_feed',
                                                  'atom_categories')
                deployment_info = self.get_deployment_info(
                    deployment_info_string)
                payload_body = ""
                if "instance.exists" in payload['event_type']:
                    service = 'nova'
                    payload_body = self.nova_cuf(deployment_info, payload)
                elif "image.exists" in payload['event_type']:
                    service = 'glance'
                    payload_body = self.glance_cuf(deployment_info, payload)
            except KeyError, e:
                error_msg = "Malformed Notification: %s" % payload
                LOG.error(error_msg)
                LOG.exception(e)
                results[msgid] = dict(error=True, code=0, message=error_msg,
                                      service=service)
                continue

            endpoint = self.config_get("url")
            tries = 0
            failures = 0
            code = 0
            ah_event_id = None
            while True:
                try:
                    response_details = connection.send_notification(endpoint, endpoint,
                                                         payload_body)
                    code = response_details.get("status")
                    ah_event_id = response_details.get("ah_event_id")
                    break
                except InvalidContentException, e:
                    LOG.exception(e)
                    LOG.error(payload_body)
                    results[msgid] = dict(error=False, code=code, message=e.msg)
                    break
                except UnauthorizedException, e:
                    LOG.exception(e)
                    connection = None
                    code = 401
                    error_msg = "Unauthorized"
                except MessageDeliveryFailed, e:
                    LOG.exception(e)
                    code = e.code
                    error_msg = e.msg
                except Exception, e:
                    code = 0 #aka 'unknown failure'
                    error_msg = "CufPub General Delivery Failure to %s with: %s" % (endpoint, e)
                    LOG.error(error_msg)
                    LOG.exception(e)

                #If we got here, something failed.
                stats.increment_stat(yagi.stats.failure_message())
                # Number of overall tries
                tries += 1
                # Number of tries between re-auth attempts
                failures += 1

                # Used primarily for testing, but it's possible we don't
                # care if we lose messages?
                if retries > 0:
                    if tries >= retries:
                        msg = "Exceeded retry limit. Error %s" % error_msg
                        results[msgid] = dict(error=False, code=code, message=msg)
                        break
                wait = min(tries * interval, max_wait)
                LOG.error("Message delivery failed, going to sleep, will "
                         "try again in %s seconds" % str(wait))
                time.sleep(wait)

                if failures >= failures_before_reauth:
                    # Don't always try to reconnect, give it a few
                    # tries first
                    failures = 0
                    connection = None
                if connection is None:
                    connection = HttpConnection(self,force=True)

            results[msgid] = dict(error=False, code=code, message="Success",
                                  service=service, ah_event_id=ah_event_id)
