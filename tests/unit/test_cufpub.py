import functools
import unittest
import httplib2
import stubout
import yagi
from yagi.handler.cuf_pub_handler import CufPub


class MockResponse(object):
    def __init__(self, status_code=200):
        self.status = status_code


class MockMessage(object):
    def __init__(self, payload):
        self.payload = payload
        self.acknowledged = False

    def ack(self):
        self.acknowledged = True


class CufPubTests(unittest.TestCase):
    """Tests to ensure the ATOM CUF Pub code holds together as expected"""

    def setUp(self):
        self.stubs = stubout.StubOutForTesting()
        config_dict = {
            'atompub': {
                'url': 'http://127.0.0.1:9000/test/%(event_type)s',
                'user': 'user',
                'key': 'key',
                'interval': 30,
                'max_wait': 600,
                'retries': 1,
                'failures_before_reauth': 5
            },
            'event_feed': {
                'feed_title': 'feed_title',
                'feed_host': 'feed_host',
                'use_https': False,
                'port': 'port',
                'atom_categories': {'DATACENTER': 'ORD1',
                                     'REGION': 'PREPROD-ORD'}

            },
            'handler_auth': {
                'method': 'no_auth'
            },
            'cufpub': {
                'url': 'http://127.0.0.1:9000/test/%(event_type)s',
                'user': 'user',
                'key': 'key',
                'interval': 30,
                'max_wait': 600,
                'retries': 1,
                'failures_before_reauth': 5

            }
        }

        self.handler = CufPub()

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

        self.stubs.Set(yagi.config, 'config_with', config_with)
        self.stubs.Set(yagi.config, 'get', get)

    def tearDown(self):
        self.stubs.UnsetAll()

    def test_notify(self):
        messages = [MockMessage(
            {
                'event_type': 'test',
                'message_id': 'some_uuid',
                '_unique_id': 'e53d007a-fc23-11e1-975c-cfa6b29bb814',
                'payload':
                    {'tenant_id': '2882',
                     'access_ip_v4': '5.79.20.138',
                     'access_ip_v6': '2a00:1a48:7804:0110:a8a0:fa07:ff08:157a',
                     'audit_period_beginning': '2012-09-15 11:51:11',
                     'audit_period_ending': '2012-09-16 11:51:11',
                     'bandwidth': {'private': {'bw_in': 0, 'bw_out': 264902},
                                   'public': {'bw_in': 1001, 'bw_out': 19992}
                                  },
                     'image_meta': {'com.rackspace__1__options': '1'},

                     'instance_id': '56',
                     'instance_type_id': '10',
                     'launched_at': '2012-09-15 12:51:11',
                     'deleted_at': ''}
            }
        )]

        self.called = False

        def mock_request(*args, **kwargs):
            self.called = True
            return MockResponse(201), None

        self.stubs.Set(httplib2.Http, 'request', mock_request)
        self.handler.handle_messages(messages, dict())
        self.assertEqual(self.called, True)

    def test_notify_fails(self):
        messages = [MockMessage(
            {
                'event_type': 'test',
                'message_id': 'some_uuid',
                '_unique_id': 'e53d007a-fc23-11e1-975c-cfa6b29bb814',
                'payload':
                    {'tenant_id': '2882',
                     'access_ip_v4': '5.79.20.138',
                     'access_ip_v6': '2a00:1a48:7804:0110:a8a0:fa07:ff08:157a',
                     'audit_period_beginning': '2012-09-15 11:51:11',
                     'audit_period_ending': '2012-09-16 11:51:11',
                     'bandwidth': {'private': {'bw_in': 0, 'bw_out': 264902},
                                   'public': {'bw_in': 1001, 'bw_out': 19992}
                                  },
                     'image_meta': {'com.rackspace__1__options': '1'},

                     'instance_id': '56',
                     'instance_type_id': '10',
                     'launched_at': '2012-09-15 12:51:11',
                     'deleted_at': ''}
            }
        )]
        self.called = False

        def mock_request(*args, **kwargs):
            self.called = True
            return MockResponse(404), None

        self.stubs.Set(httplib2.Http, 'request', mock_request)
        self.handler.handle_messages(messages, dict())
        self.assertEqual(self.called, True)

    def test_malformed_message_should_not_raise_exception(self):
        messages = [MockMessage(
            {
                'event_type': 'test',
                'message_id': 'some_uuid',
                '_unique_id': 'e53d007a-fc23-11e1-975c-cfa6b29bb814',
                'payload':
                    {'tenant_id': '2882',
                     'access_ip_v4': '5.79.20.138',
                     'access_ip_v6': '2a00:1a48:7804:0110:a8a0:fa07:ff08:157a',
                     'audit_period_beginning': '2012-09-15 11:51:11',
                     'bandwidth': {'private': {'bw_in': 0, 'bw_out': 264902},
                                   'public': {'bw_in': 1001, 'bw_out': 19992}
                                  },
                     'image_meta': {'com.rackspace__1__options': '1'},

                     'instance_id': '56',
                     'instance_type_id': '10',
                     'launched_at': '2012-09-15 12:51:11',
                     'deleted_at': ''}
            }
        )]
        self.called = False

        def mock_request(*args, **kwargs):
            self.called = True
            return MockResponse(404), None

        self.stubs.Set(httplib2.Http, 'request', mock_request)
        self.handler.handle_messages(messages, dict())
        self.assertEqual(self.called, False)

