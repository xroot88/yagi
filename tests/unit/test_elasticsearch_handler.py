import copy
import datetime
import functools
import json
import requests
import unittest2 as unittest
import uuid

import mock

import stackdistiller.distiller
import yagi.config
from yagi.handler import elasticsearch_handler


TEST_DISTILLER_CONF = [
{'event_type': 'compute.*',
  'traits': {'deleted_at': {'fields': 'payload.deleted_at',
    'type': 'datetime'},
   'host': {'fields': 'publisher_id',
    'plugin': {'name': 'split', 'parameters': {'max_split': 1, 'segment': 1}}},
   'instance_id': {'fields': 'payload.instance_id'},
   'launched_at': {'fields': 'payload.launched_at', 'type': 'datetime'},
   'service': {'fields': 'publisher_id', 'plugin': 'split'},
   'state': {'fields': 'payload.state'},
   'tenant_id': {'fields': 'payload.tenant_id'},
   'user_id': {'fields': 'payload.user_id'}}},
 {'event_type': 'compute.instance.exists',
  'traits': {'audit_period_beginning': {'fields': 'payload.audit_period_beginning',
    'type': 'datetime'},
   'audit_period_ending': {'fields': 'payload.audit_period_ending',
    'type': 'datetime'},
   'deleted_at': {'fields': 'payload.deleted_at', 'type': 'datetime'},
   'host': {'fields': 'publisher_id',
    'plugin': {'name': 'split', 'parameters': {'max_split': 1, 'segment': 1}}},
   'instance_id': {'fields': 'payload.instance_id'},
   'launched_at': {'fields': 'payload.launched_at', 'type': 'datetime'},
   'service': {'fields': 'publisher_id', 'plugin': 'split'},
   'state': {'fields': 'payload.state'},
   'tenant_id': {'fields': 'payload.tenant_id'},
   'user_id': {'fields': 'payload.user_id'}}}
]


class MockMessage(object):
    def __init__(self, payload):
        self.payload = payload
        self.acknowledged = False

    def ack(self):
        self.acknowledged = True


class TestDateEncoder(unittest.TestCase):
    def test_date_encoder(self):
        dt = datetime.datetime(2015, 5, 4, 3, 30, 41, 569321)
        expected = 1430710241569
        encoder = elasticsearch_handler.ElasticsearchDateEncoder()
        ms = encoder.default(dt)
        self.assertEqual(expected, ms)

    def test_date_encoder_json(self):
        dt = datetime.datetime(2015, 5, 4, 3, 30, 41, 569321)
        d = dict(timestamp=dt)
        j = json.dumps(d, cls=elasticsearch_handler.ElasticsearchDateEncoder)
        expected = '{"timestamp": 1430710241569}'
        self.assertEqual(expected, j)


class TestElasticsearchHandler(unittest.TestCase):

    def setUp(self):
        self.patches = []
        self.region = 'preprod'
        self.elasticsearch_host = \
            'http://127.0.0.1:9200/abacus/serverUsageEvents'
        self.distiller_config = 'event_definitions.yaml'
        config_dict = {
            'elasticsearch': {
                'region': self.region,
                'elasticsearch_host': self.elasticsearch_host,
                'distiller_config': self.distiller_config,
            },
        }

        def get(*args, **kwargs):
            val = None
            for arg in args:
                if val:
                    val = val.get(arg)
                else:
                    val = config_dict.get(arg)
                    if not val:
                        return None or kwargs.get('default')
            return val

        def config_with(*args):
            return functools.partial(get, args)

        def load_distiller_conf(filename):
            return TEST_DISTILLER_CONF

        self.patches.append(mock.patch.object(yagi.config, 'config_with',
                                              new=config_with))
        self.patches.append(mock.patch.object(yagi.config, 'get', new=get))
        self.patches.append(mock.patch.object(stackdistiller.distiller, 'load_config', new=load_distiller_conf))

        self.post_args = []

        def post(url, data=None, json=None, **kwargs):
            self.post_args.append({
                'url': url,
                'data': data,
                'json': json
            })

        self.patches.append(mock.patch.object(requests, 'post', new=post))
        for patch in self.patches:
            patch.start()

        self.handler = elasticsearch_handler.ElasticsearchHandler()

    def tearDown(self):
        for patch in self.patches:
            patch.stop()

    def test_init(self):
        self.assertEqual(self.region, self.handler.region)
        self.assertEqual(self.elasticsearch_host,
                         self.handler.elasticsearch_host)
        self.assertIsInstance(self.handler.distiller,
                              stackdistiller.distiller.Distiller)

    def test_send_to_elasticsearch_exists(self):
        begin = datetime.datetime(2015, 5, 3, 0, 0, 0, 0)
        end = datetime.datetime(2015, 5, 4, 0, 0, 0, 0)
        now = datetime.datetime.utcnow()
        message_id = str(uuid.uuid4())

        event = {
            'event_type': 'compute.instance.exists',
            'message_id': message_id,
            'audit_period_beginning': begin,
            'audit_period_ending': end,
            'when': now
        }

        expected = copy.copy(event)
        expected['region'] = self.region
        expected['@timestamp'] = end
        exp_json = json.dumps(
            expected, cls=elasticsearch_handler.ElasticsearchDateEncoder)
        expected = json.loads(exp_json)

        self.handler._send_to_elasticsearch(event)

        args = self.post_args[0]
        self.assertEqual(self.elasticsearch_host, args['url'])
        actual = json.loads(args['data'])
        self.assertDictEqual(expected, actual)

    def test_send_to_elasticsearch_other(self):
        begin = datetime.datetime(2015, 5, 3, 0, 0, 0, 0)
        end = datetime.datetime(2015, 5, 4, 0, 0, 0, 0)
        now = datetime.datetime.utcnow()
        message_id = str(uuid.uuid4())
        original_message_id = str(uuid.uuid4())

        event = {
            'event_type': 'compute.instance.exists.verified',
            'message_id': message_id,
            'original_message_id': original_message_id,
            'audit_period_beginning': begin,
            'audit_period_ending': end,
            'when': now
        }

        expected = copy.copy(event)
        expected['region'] = self.region
        expected['@timestamp'] = end
        exp_json = json.dumps(
            expected, cls=elasticsearch_handler.ElasticsearchDateEncoder)
        expected = json.loads(exp_json)

        self.handler._send_to_elasticsearch(event)

        args = self.post_args[0]
        self.assertEqual(self.elasticsearch_host, args['url'])
        actual = json.loads(args['data'])
        self.assertDictEqual(expected, actual)

    def test_handle_messages_no_cuf(self):
        exists_msg_id = str(uuid.uuid4())
        verified_msg_id = str(uuid.uuid4())
        original_message_id = exists_msg_id

        messages = [
            MockMessage({
                'event_type': 'compute.instance.exists',
                'message_id': exists_msg_id,
                'payload': {
                    'audit_period_beginning': '2015-05-03 11:51:11',
                    'audit_period_ending': '2012-05-04 11:51:11',
                }
            }),
            MockMessage({
                'event_type': 'compute.instance.exists.verified',
                'message_id': verified_msg_id,
                'original_message_id': original_message_id,
                'payload': {
                    'audit_period_beginning': '2015-05-03 11:51:11',
                    'audit_period_ending': '2012-05-04 11:51:11',
                }
            })
        ]
        env = dict()

        self.handler.handle_messages(messages, env)

        self.assertEqual(2, len(self.post_args))

    def test_handle_messages_with_cuf(self):
        exists_msg_id = str(uuid.uuid4())
        verified_msg_id = str(uuid.uuid4())
        original_message_id = exists_msg_id

        messages = [
            MockMessage({
                'event_type': 'compute.instance.exists',
                'message_id': exists_msg_id,
                'payload': {
                    'audit_period_beginning': '2015-05-03 11:51:11',
                    'audit_period_ending': '2012-05-04 11:51:11',
                }
            }),
            MockMessage({
                'event_type': 'compute.instance.exists.verified',
                'message_id': verified_msg_id,
                'original_message_id': original_message_id,
                'payload': {
                    'audit_period_beginning': '2015-05-03 11:51:11',
                    'audit_period_ending': '2012-05-04 11:51:11',
                }
            })
        ]
        env = dict()
        cuf_results = env.setdefault('cufpub.results', dict())
        cuf_results[verified_msg_id] = dict(error=False, code=None,
                                            message="Success", service='novae',
                                            ah_event_id='some_ah_event_id')

        self.handler.handle_messages(messages, env)

        self.assertEqual(3, len(self.post_args))
        args = self.post_args[2]
        actual = json.loads(args['data'])
        self.assertEqual('compute.instance.exists.verified.cuf',
                         actual['event_type'])
        self.assertEqual(verified_msg_id, actual['original_message_id'])
