import json
import requests
import time

import yagi.config
import yagi.handler
import yagi.log

with yagi.config.defaults_for("stacktach") as default:
    default("timeout", "120")
    default("url", "http://127.0.0.1/db/confirm/usage/exists/batch")

LOG = yagi.log.logger


class StackTachPing(yagi.handler.BaseHandler):
    CONFIG_SECTION = "stacktach"

    def handle_messages(self, messages, env):
        atompub_results = env.get('atompub.results')
        ping = dict()

        if atompub_results is None:
            LOG.error("Stacktack ping handler cannot find results from atompub!")
            return

        for payload in self.iterate_payloads(messages, env):
            msgid = payload["message_id"]
            st = atompub_results.get(msgid)
            code = 0
            if st is not None:
                code = st['code']
            ping[msgid] = code
        url =  self.config_get("url")
        status = self._post_to_st(url, ping)

    def _check_return(self, status):
        return status == requests.codes.ok

    def _post_to_st(self, url, ping):
        timeout =  int(self.config_get("timeout"))
        data = json.dumps(dict(messages=ping))
        try:
            res = requests.put(url, data=data,
                               timeout=timeout,
                               allow_redirects=True)
        except requests.exceptions.Timeout:
            LOG.error("Timeout pinging stacktach")
        if not self._check_return(res.status_code):
            LOG.error("Error posting to StackTach: %s" % res.status_code)
            LOG.error("Error message from StackTach: %s" % res.text)
        return res.status_code

