import copy
from datetime import datetime
import json
import logging
import requests

import pytz

import stackdistiller.distiller
import yagi
import yagi.serializer.cuf


LOG = logging.getLogger(__name__)


# Note: There is a similar class in stacktach-notifiction-utils, however
# it renders datetime objects as a string with <seconds>.<microseconds>.
# Elasticsearch doesn't understand microseconds in timestamps so we need
# a different format. Numeric milliseconds work well.
class ElasticsearchDateEncoder(json.JSONEncoder):
    def datetime_ms(self, dt):
        """Encodes a datetime object as milliseconds since the epoch.
        :param dt: The datetime to be encoded
        :return: The datetime as milliseconds since the epoch"""
        epoch = datetime.utcfromtimestamp(0)
        if dt.tzinfo is not None:
            epoch = epoch.replace(tzinfo=pytz.UTC)

        delta = dt - epoch

        seconds = int(delta.total_seconds())
        ms = (seconds * 1000) + (dt.microsecond / 1000)
        return ms

    def default(self, o):
        if isinstance(o, datetime):
            return self.datetime_ms(o)

        return super(ElasticsearchDateEncoder, self).default(o)


class ElasticsearchHandler(yagi.handler.BaseHandler):
    CONFIG_SECTION = 'elasticsearch'
    AUTO_ACK = True

    def __init__(self, app=None, queue_name=None):
        super(ElasticsearchHandler, self).__init__(app=app,
                                                   queue_name=queue_name)
        self.region = self.config_get('region')
        self.elasticsearch_host = self.config_get('elasticsearch_host')
        dist_conf_file = self.config_get('distiller_config')
        dist_conf = stackdistiller.distiller.load_config(dist_conf_file)
        self.distiller = stackdistiller.distiller.Distiller(dist_conf)

    def _send_to_elasticsearch(self, event):
        if 'compute.instance.exists' == event['event_type']:
            event['@timestamp'] = event['audit_period_ending']
        else:
            event['@timestamp'] = event['when']

        event['region'] = self.region

        json_event = json.dumps(event, cls=ElasticsearchDateEncoder)
        try:
            LOG.debug('Sending to Elasticsearch: %s' % json_event)
            requests.post(self.elasticsearch_host, data=json_event)
        except Exception:
            LOG.exception('Error sending event to Elasticsearch')

    def handle_messages(self, messages, env):
        cuf_pub_results = env.setdefault('cufpub.results', dict())
        verified_msg_ids = []
        for payload in self.iterate_payloads(messages, env):
            try:
                if 'instance.exists' in payload['event_type']:
                    LOG.debug('Found event of type: %s' %
                              payload['event_type'])
                    event = self.distiller.to_event(payload)
                    self._send_to_elasticsearch(event.get_event())
                    if ('compute.instance.exists.verified' ==
                            payload['event_type']):
                        verified_msg_ids.append(payload['message_id'])
            except KeyError:
                error_msg = 'Malformed Notification: %s' % payload
                LOG.exception(error_msg)
                continue

        # Look for successful cuf_pub results and push fake 'events' to ES
        for msgid in verified_msg_ids:
            result = cuf_pub_results.get(msgid)
            if result is not None:
                if not result['error'] and ('Success' == result['message']):
                    LOG.debug('Synthesizing .cuf event for ah event: %s' %
                              result['ah_event_id'])
                    event = copy.copy(result)
                    event['when'] = datetime.utcnow().replace(tzinfo=pytz.UTC)
                    event['original_message_id'] = msgid
                    event['event_type'] = \
                        'compute.instance.exists.verified.cuf'
                    event['message_id'] = event['ah_event_id']
                    self._send_to_elasticsearch(event)
