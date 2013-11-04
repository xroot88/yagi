import functools
import unittest

import requests
import stubout
import json

import yagi.config

from yagi.handler.stacktach_ping_handler import StackTachPing


class MockResponse(object):
    def __init__(self, status_code=200):
        self.status_code = status_code
        self.text = "Ka-Splat!!"


class MockMessage(object):
    def __init__(self, payload):
        self.payload = payload
        self.acknowledged = False

    def ack(self):
        self.acknowledged = True


class StackTachPingTests(unittest.TestCase):
    """Tests to ensure the Stachtach ping handler works"""

    def setUp(self):
        self.stubs = stubout.StubOutForTesting()
        self.config_dict = {
            'stacktach': {
                'url': 'http://127.0.0.1:9000/db/confirm/usage/exists/batch',
                'timeout': '120',
                "ping_events": "*",
                "results_from": "atompub.results",
            },
        }

        self.handler = StackTachPing()
        self.messages = [MockMessage({'event_type': 'compute.instance.create',
                    'message_id': '1',
                    'content': dict(a=3)}),
                    MockMessage({'event_type': 'compute.instance.delete',
                    'message_id': '2',
                    'content': dict(a=42)}),
                    ]
        self.mock_env = {'atompub.results':
                      {'1' : dict(code=201, error=False, message="yay",
                                  service="nova"),
                       '2' : dict(code=404, error=False, message="boo",
                                  service="nova")}}

        self.called = False
        self.data = None

        def get(*args, **kwargs):
            val = None
            for arg in args:
                if val:
                    val = val.get(arg)
                else:
                    val = self.config_dict.get(arg)
                    if not val:
                        return None or kwargs.get('default')
            return val

        def config_with(*args):
            return functools.partial(get, args)

        self.stubs.Set(yagi.config, 'config_with', config_with)
        self.stubs.Set(yagi.config, 'get', get)

    def tearDown(self):
        self.stubs.UnsetAll()

    def test_ping(self):

        def mock_put(url, data=None, **kw):
            self.called = True
            self.data = data
            return MockResponse(201)

        self.stubs.Set(requests, 'put', mock_put)
        self.stubs.Set(requests.codes, 'ok', 201)

        self.handler.handle_messages(self.messages, self.mock_env)
        self.assertTrue(self.called)
        val = json.loads(self.data)
        self.assertTrue('messages' in val)
        self.assertEqual(len(val['messages']), 2)
        self.assertEqual(val['messages']['1']['code'], 201)
        self.assertEqual(val['messages']['2']['code'], 404)

    def test_ping_fails(self):
        #make sure it doesn't blow up if stacktach is borked.

        def mock_put(url, data=None, **kw):
            self.called = True
            self.data = data
            return MockResponse(500)

        self.stubs.Set(requests, 'put', mock_put)
        self.stubs.Set(requests.codes, 'ok', 201)

        self.handler.handle_messages(self.messages, self.mock_env)
        self.assertTrue(self.called)

    def test_match_event(self):
        matched = []
        conf = self.config_dict['stacktach']
        conf['ping_events'] = "compute.instance.create"
        for payload in self.handler.iterate_payloads(self.messages,
                                                     self.mock_env):
            #should match all of them
            if self.handler.match_event(payload):
                matched.append(payload)

        self.assertEqual(len(matched), 1)

    def test_match_event_wildcard(self):
        matched = []
        for payload in self.handler.iterate_payloads(self.messages,
                                                     self.mock_env):
            #should match all of them
            if self.handler.match_event(payload):
                matched.append(payload)

        self.assertEqual(len(matched), len(self.messages))

    def test_get_results(self):
        results = self.handler.get_results(self.mock_env)
        self.assertTrue('atompub.results' in results)
        self.assertEqual(len(results),1)


