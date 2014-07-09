import json

import httplib2
import logging

import yagi.config


LOG = logging.getLogger(__name__)


token = None


def no_auth(*args, **kwargs):
    pass


def http_basic_auth(conn, headers, force=False):
    user = yagi.config.get("handler_auth", "user")
    key = yagi.config.get("handler_auth", "key")
    if user and key:
        conn.add_credentials(user, key)


def _rax_auth(conn, headers, force, build_auth_body):
    global token
    if force or not token:
        user = yagi.config.get("handler_auth", "user")
        key = yagi.config.get("handler_auth", "key")
        ssl_check = not (yagi.config.get("handler_auth", "validate_ssl",
            default=False) == "True")
        auth_server = yagi.config.get("handler_auth", "auth_server")
        req = httplib2.Http(disable_ssl_certificate_validation=ssl_check)
        body = build_auth_body(user, key)
        auth_headers = {}
        auth_headers["User-Agent"] = "Yagi"
        auth_headers["Accept"] = "application/json"
        auth_headers["Content-Type"] = "application/json"
        req.follow_all_redirects = True
        LOG.info("Contacting RAX auth server %s" % auth_server)
        LOG.debug("Request for call %r" % auth_headers)
        LOG.debug("Body for call %r" % body)
        res, body = req.request(auth_server, "POST", body=json.dumps(body),
            headers=auth_headers)
        LOG.debug("Respsonse from call %r" % res)
        LOG.debug("Body from call %r" % body)
        # Why 200? it's creating something :-/
        if res.status != 200:
            raise Exception("Authentication failed with HTTP Status %d" %
                            res.status)
        token = json.loads(body)["access"]["token"]["id"]
        LOG.info("Token received: %s" % token)
    headers["X-Auth-Token"] = token


def rax_auth(conn, headers, force=False):
    def _auth_body(user, key):
        return {"auth": {
                "passwordCredentials": {
                    "username": user,
                    "password": key,
                }}}
    _rax_auth(conn, headers, force, _auth_body)


def rax_auth_v2(conn, headers, force=False):
    def _auth_body(user, key):
        return {"auth": {
                "RAX-KSKEY:apiKeyCredentials": {
                    "username": user,
                    "apiKey": key,
                }}}
    _rax_auth(conn, headers, force, _auth_body)


def get_auth_method(method=None):
    if not method:
        method = yagi.config.get("handler_auth", "method")
    if method in globals():
        return globals()[method]
    return None
