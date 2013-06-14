from yagi import http_util
import time

import yagi.auth
import yagi.config
import yagi.handler
from yagi.handler.atompub_handler import UnauthorizedException, MessageDeliveryFailed
import yagi.log
import yagi.serializer.atom

with yagi.config.defaults_for("cufpub") as default:
    default("validate_ssl", "False")
    default("retries", "-1")
    default("url", "http://127.0.0.1/nova")
    default("max_wait", "600")
    default("failures_before_reauth", "5")
    default("interval", "30")

LOG = yagi.log.logger


class HttpConnection():
    def __init__(self,handler,force=False):
        ssl_check = not (handler.config_get("validate_ssl") == "True")
        self.conn = http_util.LimitingBodyHttp(
                        disable_ssl_certificate_validation=ssl_check)
        auth_method = yagi.auth.get_auth_method()
        self.headers = {}
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
        conn = self.conn
        headers = self.headers
        LOG.debug("Sending message to %s with body: %s" % (endpoint, body))
        self.headers["Content-Type"] = "application/atom+xml"
        try:
            resp, content = conn.request(endpoint, "POST",
                                         body=body,
                                         headers=headers)
            if resp.status == 401:
                raise UnauthorizedException("Unauthorized or token expired")
            if resp.status != 201:
                msg = ("AtomPub resource create failed for %s Status: "
                            "%s, %s" % (puburl, resp.status, content))
                raise MessageDeliveryFailed(msg, resp.status)
            return resp.status
        except http_util.ResponseTooLargeError, e:
            if e.response.status == 201:
                # Was successfully created. Reply was just too large.
                # Note that we DON'T want to retry this if we've gotten a 201.
                LOG.error("Response too large on successful post")
                LOG.exception(e)
            else:
                msg = ("AtomPub resource create failed for %s. "
                       "Also, response was too large." % puburl )
                raise MessageDeliveryFailed(msg, e.response.status)