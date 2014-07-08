import json
import logging
import requests
import time

import yagi.config
import yagi.handler

with yagi.config.defaults_for("stacktach") as default:
    default("timeout", "120")
    default("url", "http://127.0.0.1/db/confirm/usage/exists/batch")
    default("ping_events", "compute.instance.exists.verified.old")
    default("results_from", "atompub.results")

LOG = logging.getLogger(__name__)


class StackTachPing(yagi.handler.BaseHandler):
    CONFIG_SECTION = "stacktach"

    @property
    def matching_events(self):
        events = self.config_get('ping_events')
        return [e.strip() for e in events.split(',')]

    @property
    def results_from(self):
        result_names = self.config_get('results_from')
        return [e.strip() for e in result_names.split(',')]

    def match_event(self, payload):
        event_type = payload.get('event_type')
        for e in self.matching_events:
            if event_type == e:
                return True
            if e == '*':
                return True
        return False

    def get_results(self, env):
        names = self.results_from
        results = dict(((r, env.get(r)) for r in names if r in env))
        for n in names:
            if n not in env:
                LOG.error("Stacktack ping handler cannot"
                          " find results from %s!" % n)
        return results

    def handle_messages(self, messages, env):
        results = self.get_results(env)
        if not results:
            LOG.error("Stacktack ping handler cannot find any results!")
            return
        pings = dict((n, {'nova': {}, 'glance': {}})
                     for n in results)
        for payload in self.iterate_payloads(messages, env):
            if self.match_event(payload):
                ping_msgid = msgid = payload["message_id"]
                if 'original_message_id' in payload:
                    ping_msgid = payload['original_message_id']
                for result in results:
                    st = results[result].get(msgid)
                    if st is not None:
                        code = st['code']
                        service = st['service']
                        event_id = st.get('ah_event_id')
                        pings[result][service][ping_msgid] = {'status': code}
                        if event_id:
                            pings[result][service][ping_msgid]['event_id'] = event_id
        url = self.config_get("url")
        for ping in pings.values():
            if ping:
                self._post_to_st(url, ping)

    def _check_return(self, status):
        return status == requests.codes.ok

    def _post_to_st(self, url, ping):
        timeout = int(self.config_get("timeout"))
        data = json.dumps(dict(messages=ping, version=2))
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

