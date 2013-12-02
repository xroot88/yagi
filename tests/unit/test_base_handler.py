import functools
import unittest
import mox
import stubout
import yagi
from yagi.handler import cuf_pub_handler, atompub_handler
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


class BaseHandlerTests(unittest.TestCase):
    """Tests to ensure the ATOM CUF Pub code holds together as expected"""

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

        },
        'filters' : {
            'cufpub': 'compute.instance.exists.verified, compute.instance.exists'
        },
        'exclude_filters' : {}
    }

    def setUp(self):
        self.mox = mox.Mox()
        self.stubs = stubout.StubOutForTesting()

        self.handler = CufPub()

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
        self.mox.UnsetStubs()
        self.stubs.UnsetAll()

    def test_filter_out_exists_messages_for_cuf_handler(self):
        mock_message1 = MockMessage(
            {
                'event_type': 'compute.instance.exists',
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
        )
        mock_message2 = MockMessage(
            {
                'event_type': 'compute.instance.exists.verified',
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
        )
        mock_message3 = MockMessage(
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
        )
        messages = [mock_message1,mock_message2,mock_message3]
        filtered_messages= [mock_message1,mock_message2]
        cuf_pub = cuf_pub_handler.CufPub()
        self.mox.StubOutWithMock(cuf_pub, 'handle_messages')
        cuf_pub.handle_messages(filtered_messages,env=dict())
        self.mox.ReplayAll()
        cuf_pub(messages, dict())
        self.mox.VerifyAll()

    def test_filter_should_not_be_applied_if_not_declared_in_config(self):
        mock_message1 = MockMessage(
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
        )
        messages = [mock_message1]
        filtered_messages= [mock_message1]
        atom_pub = atompub_handler.AtomPub()
        self.config_dict['exclude_filters'] = {
            "atompub": {}}
        self.mox.StubOutWithMock(atom_pub, 'handle_messages')
        atom_pub.handle_messages(filtered_messages,env=dict())
        self.mox.ReplayAll()
        atom_pub(messages, dict())
        self.mox.VerifyAll()

    def test_exclude_filter_discards_message(self):
        mock_message1 = MockMessage(
            {
                'event_type': 'compute.instance.exists',
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
        )
        mock_message2 = MockMessage(
            {
                'event_type': 'image.exists.verified',
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
        )
        mock_message3 = MockMessage(
            {
                'event_type': 'compute.instance.exists',
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
        )
        self.config_dict['exclude_filters'] = {
            "atompub": 'image.exists.verified'}
        messages = [mock_message1, mock_message2, mock_message3]
        filtered_messages= [mock_message1, mock_message3]
        atom_pub = atompub_handler.AtomPub()
        self.mox.StubOutWithMock(atom_pub, 'handle_messages')
        atom_pub.handle_messages(filtered_messages,env=dict())
        self.mox.ReplayAll()
        atom_pub(messages, dict())
        self.mox.VerifyAll()

