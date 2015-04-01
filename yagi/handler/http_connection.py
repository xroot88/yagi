import BeautifulSoup
import logging

from yagi import http_util
import time

import yagi.auth
import yagi.config
import yagi.handler
import yagi.serializer.atom

LOG = logging.getLogger(__name__)

class MessageDeliveryFailed(Exception):
    def __init__(self, msg, code, *args):
        self.code = code
        self.msg = msg
        args = (msg, code) + args
        super(MessageDeliveryFailed, self).__init__(*args)


class UnauthorizedException(Exception):
    pass


class InvalidContentException(Exception):
    def __init__(self, msg, code, *args):
        self.code = code
        self.msg = msg
        args = (msg, code) + args
        super(InvalidContentException, self).__init__(*args)


class HttpConnection():
    def __init__(self, handler,force=False):
        ssl_check = not (handler.config_get("validate_ssl") == "True")
        timeout = int(handler.config_get('timeout', default=120))
        self.conn = http_util.LimitingBodyHttp(timeout=timeout,
                        disable_ssl_certificate_validation=ssl_check)
        auth_method = yagi.auth.get_auth_method()
        self.headers = {}
        self.handler = handler.CONFIG_SECTION
        if auth_method:
            try:
                auth_method(self.conn, self.headers, force=force)
            except Exception, e:
                # Auth could be jacked for some reason, slow down on failing.
                # Alternatively, if we have bad credentials, don't fill
                # up the logs crying about it.
                LOG.exception(e)
                interval = int(handler.config_get("interval"))
                time.sleep(interval)
        else:
            raise Exception("Invalid auth or no auth supplied")

    def send_notification(self, endpoint, puburl, body):
        LOG.info("Sending message to %s with body: %s" % (endpoint, body))
        self.headers["Content-Type"] = "application/atom+xml"
        try:
            resp, content = self.conn.request(endpoint, "POST",
                                              body=body,
                                              headers=self.headers)
            response_details = {"status": resp.status}
            if resp.status == 201:
                parsed_content = BeautifulSoup.BeautifulSoup(content)
                id_tag = "?"
                atom_id_tag = parsed_content.find('atom:id')
                if atom_id_tag:
                    ah_event_id = atom_id_tag.string.replace('urn:uuid:', '')
                    response_details.update({"ah_event_id": ah_event_id})
                elif "compute.instance.exists.verified" in parsed_content.find("title"):
                    id_tag = parsed_content.find('id')
                    if id_tag:
                        ah_event_id = id_tag.string.replace('urn:uuid:', '')
                        response_details.update({"ah_event_id": ah_event_id})
                LOG.info("Successfully sent - ah_event_id: %s (%s, %s)" %
                                    (ah_event_id, atom_id_tag, id_tag))
            if resp.status == 401:
                raise UnauthorizedException("Unauthorized or token expired")
            if resp.status == 409:
                #message id already exists. this is a dup, don't resend.
                return response_details
            if resp.status == 400:
                msg = ("%s resource create failed for %s Status: "
                            "%s, %s" % (self.handler, puburl, resp.status,
                                        content))
                raise InvalidContentException(msg, resp.status)
            if resp.status != 201:
                msg = ("%s resource create failed for %s Status: "
                            "%s, %s" % (self.handler, puburl, resp.status,
                                        content))
                raise MessageDeliveryFailed(msg, resp.status)
            return response_details
        except http_util.ResponseTooLargeError, e:
            if e.response.status == 201:
                # Was successfully created. Reply was just too large.
                # Note that we DON'T want to retry this if we've gotten a 201.
                LOG.error("Response too large on successful post")
                LOG.exception(e)
            else:
                msg = ("%s resource create failed for %s. "% (self.handler,
                                                              puburl),
                       "Also, response was too large.")
                raise MessageDeliveryFailed(msg, e.response.status)
