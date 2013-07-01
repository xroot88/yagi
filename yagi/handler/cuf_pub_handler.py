import os
import time
import uuid
from yagi import stats
import yagi
from yagi.config import config
from yagi.handler.http_connection import HttpConnection
from yagi.handler.http_connection import MessageDeliveryFailed
from yagi.handler.http_connection import UnauthorizedException
from yagi.handler.notification import Notification
import yagi.serializer.cuf

LOG = yagi.log.logger


class CufPub(yagi.handler.BaseHandler):
    CONFIG_SECTION = "cufpub"
    AUTO_ACK = True

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
                deployment_info = yagi.config.get('event_feed',
                                                  'atom_categories')
                cuf = Notification(payload).\
                    convert_to_verified_message_in_cuf_format(
                    {'region': deployment_info['DATACENTER'],
                     'data_center': deployment_info['REGION']})
                entity = dict(content=cuf,
                              id=str(uuid.uuid4()),
                              event_type='compute.instance.exists.verified')
                payload_body = yagi.serializer.cuf.dump_item(entity)
            except KeyError, e:
                error_msg = "Malformed Notification: %s" % payload
                LOG.error(error_msg)
                LOG.exception(e)
                results[msgid] = dict(error=True, code=0, message=error_msg)
                continue

            endpoint = self.config_get("url")
            tries = 0
            failures = 0
            code = 0

            while True:
                try:
                    code = connection.send_notification(endpoint, endpoint,
                                                         payload_body)
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

            results[msgid] = dict(error=False, code=code, message="Success")
