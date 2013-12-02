import functools
import unittest
import uuid

import httplib2
import mox
import stubout

import yagi.config

from yagi.handler.atompub_handler import AtomPub


class MockResponse(object):
    def __init__(self, status_code=200):
        self.status = status_code


class MockMessage(object):
    def __init__(self, payload):
        self.payload = payload
        self.acknowledged = False

    def ack(self):
        self.acknowledged = True


class AtomPubTests(unittest.TestCase):
    """Tests to ensure the ATOM Pub code holds together as expected"""
    config_dict = {
        'atompub': {
            'url': 'http://127.0.0.1:9000/test/%(event_type)s',
            'user': 'user',
            'key': 'key',
            'interval': 30,
            'max_wait': 600,
            'retries': 1,
            'failures_before_reauth': 5,
            'stacktach_down': 'False'
        },
        'event_feed': {
            'feed_title': 'feed_title',
            'feed_host': 'feed_host',
            'use_https': False,
            'port': 'port'
        },
        'handler_auth': {
            'method': 'no_auth'
        },
        'exclude_filters': {
          'atompub': {}
        }
    }

    def setUp(self):
        self.stubs = stubout.StubOutForTesting()
        self.handler = AtomPub()
        self.mox = mox.Mox()

        def get(*args, **kwargs):
            val = None
            for arg in args:
                if val:
                    val = val.get(arg)
                else:
                    val = AtomPubTests.config_dict.get(arg)
                    if not val:
                        return None or kwargs.get('default')
            return val

        def config_with(*args):
            return functools.partial(get, args)

        self.stubs.Set(yagi.config, 'config_with', config_with)
        self.stubs.Set(yagi.config, 'get', get)

    def tearDown(self):
        self.stubs.UnsetAll()
        self.mox.UnsetStubs()

    def test_notify(self):
        messages = [MockMessage({'event_type': 'instance_create',
                    'message_id': 1,
                    'content': dict(a=3)})]

        self.called = False

        def mock_request(*args, **kwargs):
            self.called = True
            return MockResponse(201), None

        self.stubs.Set(httplib2.Http, 'request', mock_request)
        self.handler.handle_messages(messages, dict())
        self.assertEqual(self.called, True)

    def test_notify_fails(self):
        messages = [MockMessage({'event_type': 'instance_create',
                    'message_id': 1,
                    'content': dict(a=3)})]
        self.called = False

        def mock_request(*args, **kwargs):
            self.called = True
            return MockResponse(404), None

        self.stubs.Set(httplib2.Http, 'request', mock_request)
        self.handler.handle_messages(messages, dict())
        self.assertEqual(self.called, True)

    def test_send_exists_and_exists_verified_when_stacktach_down(self):
        message_id = 1
        exists_payload = {'event_type': 'compute.instance.exists',
                          'message_id': message_id, 'content': dict(a=3)}
        exists_verified_payload = {
            'event_type': 'compute.instance.exists.verified',
            'message_id': message_id, 'content': dict(a=3)}
        messages = [MockMessage(exists_payload)]
        self.called = False

        def mock_request(*args, **kwargs):
            self.called = True
            return MockResponse(404), None

        AtomPubTests.config_dict['atompub']['stacktach_down'] = 'True'
        new_message_id = '16fd2706-8baf-433b-82eb-8c7fada847da'
        self.mox.StubOutWithMock(uuid, 'uuid4')
        uuid.uuid4().AndReturn(new_message_id)
        self.mox.StubOutWithMock(yagi.serializer.atom, 'dump_item')
        expected_verified_entity = {
                    'event_type': 'compute.instance.exists.verified',
                    'id': new_message_id,
                    'content': exists_verified_payload}
        expected_exists_entity = {
                    'event_type': 'compute.instance.exists',
                    'id': message_id,
                    'content': exists_payload}
        yagi.serializer.atom.dump_item(expected_verified_entity,
                                       entity_links=False)
        yagi.serializer.atom.dump_item(expected_exists_entity,
                                       entity_links=False)
        self.mox.ReplayAll()
        self.stubs.Set(httplib2.Http, 'request', mock_request)
        self.handler.handle_messages(messages, dict())
        self.mox.VerifyAll()
        self.assertEqual(self.called, True)

    def test_send_only_exists_when_stacktach_down(self):
        payload = {'event_type': 'compute.instance.exists', 'message_id': 1,
                   'content': dict(a=3)}
        messages = [MockMessage(payload)]
        self.called = False

        def mock_request(*args, **kwargs):
            self.called = True
            return MockResponse(404), None

        AtomPubTests.config_dict['atompub']['stacktach_down'] = 'True'
        AtomPubTests.config_dict['exclude_filters']['atompub'] = \
            'compute.instance.exists.verified'
        self.mox.StubOutWithMock(yagi.serializer.atom, 'dump_item')
        expected_entity = {
                    'event_type': 'compute.instance.exists',
                    'id': 1,
                    'content': payload}
        yagi.serializer.atom.dump_item(expected_entity, entity_links=False)
        self.mox.ReplayAll()
        self.stubs.Set(httplib2.Http, 'request', mock_request)
        self.handler.handle_messages(messages, dict())
        self.mox.VerifyAll()
        self.assertEqual(self.called, True)

    def test_do_not_change_other_events_to_verified_when_stacktach_down(self):
        payload = {'event_type': 'compute.instance.random', 'message_id': 1,
                   'content': dict(a=3)}
        messages = [MockMessage(payload)]
        self.called = False

        def mock_request(*args, **kwargs):
            self.called = True
            return MockResponse(404), None

        AtomPubTests.config_dict['atompub']['stacktach_down'] = 'True'
        self.mox.StubOutWithMock(yagi.serializer.atom, 'dump_item')
        expected_entity = {
                    'event_type': 'compute.instance.random',
                    'id': 1,
                    'content': payload}
        yagi.serializer.atom.dump_item(expected_entity, entity_links=False)
        self.mox.ReplayAll()
        self.stubs.Set(httplib2.Http, 'request', mock_request)
        self.handler.handle_messages(messages, dict())
        self.mox.VerifyAll()
        self.assertEqual(self.called, True)
