import functools
import unittest
import uuid
import httplib2
import mox
import stubout
from yagi.handler import http_connection
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
        self.mox = mox.Mox()
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
                'atom_categories': "DATACENTER=ORD1, REGION=PREPROD-ORD"

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
            'nova': {
                'nova_flavor_field_name': 'dummy_flavor_field_name'
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
        self.mox.UnsetStubs()

    def test_notify_for_instance_exists_message(self):
        messages = [MockMessage(
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
                     'bandwidth': {'private': {'bw_in': '0', 'bw_out': '264902'},
                                   'public': {'bw_in': '1001', 'bw_out': '19992'}
                                  },
                     'image_meta': {'com.rackspace__1__options': '1'},

                     'instance_id': '56',
                     'dummy_flavor_field_name': '10',
                     'launched_at': '2012-09-15 12:51:11',
                     'deleted_at': ''}
            }
        )]

        body = ("""<?xml version="1.0" encoding="utf-8"?>\n<?atom """
        """feed="glance/events"?><atom:entry xmlns="http://www.w3.org"""
        """/2005/Atom"><category term="compute.instance.exists.verified.cuf">"""
        """</category><atom:title type="text">Server</atom:title>"""
        """<atom:content type="application/xml">&lt;event xmlns="http://"""
        """docs.rackspace.com/core/event" xmlns:nova="http://docs"""
        """.rackspace.com/event/nova" version"""
        """="1" tenantId="2882" id="e53d007a-fc23-11e1-975c-cfa6b29bb814" """
        """resourceId="56" type="USAGE" dataCenter="PREPROD-ORD" """
        """region="ORD1" startTime="2012-09-15 12:51:11" """
        """endTime="2012-09-16 11:51:11"&gt;&lt;nova:product version="1" """
        """serviceCode="CloudServersOpenStack" resourceType="SERVER" """
        """flavor="10" isRedHat="true" isMSSQL="false" isMSSQLWeb="false" """
        """isWindows="false" isSELinux="false" isManaged="false" """
        """bandwidthIn="1001" bandwidthOut="19992"/&gt;&lt;/event&gt"""
        """;</atom:content></atom:entry></atom>""")
        self.mox.StubOutWithMock(httplib2.Http, """request""")
        httplib2.Http.request('http://127.0.0.1:9000/test/%(event_type)s',
                              'POST', body=body,
                              headers={'Content-Type': 'application/atom+xml'}
        ).AndReturn((MockResponse(201), None))

        self.mox.ReplayAll()

        self.handler.handle_messages(messages, dict())

        self.mox.VerifyAll()

    def test_notify_for_image_exists_message_for_one_image(self):
        messages = [MockMessage(
            {"event_type": "image.exists",
            "timestamp": "2013-09-02 16:09:16.247932",
            "message_id": "18b59543-2e99-4208-ba53-22726c02bd67",
            "priority": "INFO",
            "publisher_id": "ubuntu",
            "payload": {
                "owner": "owner1",
                "audit_period_ending": "2013-09-02 23:59:59.999999",
                "audit_period_beginning": "2013-09-02 00:00:00",
                "images": [{
                    "status": "active",
                    "name": "image1",
                    "created_at": "2013-09-02 16:08:10",
                    "properties": {
                        "image_type": "snapshot",
                        "instance_uuid": "inst_uuid1"
                    },
                    "deleted_at": None,
                    "id": "image1",
                    "size": 12345
                }]
        }}
        )]

        cuf_xml_body = ("""<?xml version="1.0" encoding="utf-8"?>\n<?atom """
        """feed="glance/events"?><atom:entry xmlns="http://docs.rackspace."""
        """com/core/event" xmlns:atom="http://www.w3.org/2005/Atom" """
        """xmlns:glance="http://docs.rackspace.com/usage/glance">"""
        """<category term="image.exists.verified.cuf"></category>"""
        """<atom:title type="text">Glance"""
        """</atom:title><atom:content type="application/xml">&lt;events&gt;&lt;"""
        """event endTime="2013-09-02 23:59:59.999999" """
        """startTime="2013-09-02 16:08:10" region="ORD1" """
        """dataCenter="PREPROD-ORD" type="USAGE" """
        """id="a70508f3-7254-4abc-9e14-49de6bb4d628" resourceId="image1" """
        """tenantId="owner1" version="1"&gt; &lt;glance:product """
        """storage="12345" serverId="inst_uuid1" serviceCode="Glance" """
        """serverName="" resourceType="snapshot" version="1"/&gt;&lt;/event&gt;&lt;/events&gt;"""
        """</atom:content></atom:entry></atom>""")

        self.mox.StubOutWithMock(httplib2.Http, 'request')
        httplib2.Http.request('http://127.0.0.1:9000/test/%(event_type)s',
                              'POST', body=cuf_xml_body,
                              headers={'Content-Type': 'application/atom+xml'}
        ).AndReturn((MockResponse(201), None))
        self.mox.StubOutWithMock(uuid, 'uuid4')
        uuid.uuid4().AndReturn("a70508f3-7254-4abc-9e14-49de6bb4d628")
        uuid.uuid4().AndReturn("a70508f3-7254-4abc-9e14-49de6bb4d628")
        self.mox.ReplayAll()

        self.handler.handle_messages(messages, dict())

        self.mox.VerifyAll()

    def test_notify_for_image_exists_message_for_more_than_one_image(self):
        messages = [MockMessage(
            {"event_type": "image.exists",
            "timestamp": "2013-09-02 16:09:16.247932",
            "message_id": "18b59543-2e99-4208-ba53-22726c02bd67",
            "priority": "INFO",
            "publisher_id": "ubuntu",
            "payload": {
                "owner": "owner1",
                "audit_period_ending": "2013-09-02 23:59:59.999999",
                "audit_period_beginning": "2013-09-02 00:00:00",
                "images": [{
                    "status": "active",
                    "name": "image1",
                    "created_at": "2013-09-02 16:08:10",
                    "properties": {
                        "image_type": "snapshot",
                        "instance_uuid": "inst_uuid1"
                    },
                    "deleted_at": None,
                    "id": "image1",
                    "size": 12345
                },
                {
                    "status": "deleted",
                    "name": "image2",
                    "created_at": "2013-09-02 16:05:17",
                    "properties": {
                        "image_type": "snapshot",
                        "instance_uuid": "inst_uuid2"
                    },
                    "deleted_at": "2013-09-02 16:08:46",
                    "id": "image2",
                    "size": 67890
                }]
        }}
        )]

        cuf_xml_body = ("""<?xml version="1.0" encoding="utf-8"?>\n<?atom """
        """feed="glance/events"?><atom:entry xmlns="http://docs.rackspace."""
        """com/core/event" xmlns:atom="http://www.w3.org/2005/Atom" """
        """xmlns:glance="http://docs.rackspace.com/usage/glance">"""
        """<category term="image.exists.verified.cuf"></category>"""
        """<atom:title type="text">Glance</atom:title><atom:content type="application/xml">"""
        """&lt;events&gt;&lt;event endTime="2013-09-02 23:59:59.999999" startTime="2013-09-02 """
        """16:08:10" region="ORD1" dataCenter="PREPROD-ORD" type="USAGE" """
        """id="a70508f3-7254-4abc-9e14-49de6bb4d628" resourceId="image1" """
        """tenantId="owner1" version="1"&gt; &lt;glance:product storage="12345" """
        """serverId="inst_uuid1" serviceCode="Glance" serverName="" """
        """resourceType="snapshot" version="1"/&gt;&lt;/event&gt;&lt;event """
        """endTime="2013-09-02 16:08:46" startTime="2013-09-02 16:05:17" """
        """region="ORD1" dataCenter="PREPROD-ORD" type="USAGE" """
        """id="a70508f3-7254-4abc-9e14-49de6bb4d628" resourceId="image2" """
        """tenantId="owner1" version="1"&gt; &lt;glance:product storage="67890" """
        """serverId="inst_uuid2" serviceCode="Glance" serverName="" """
        """resourceType="snapshot" version="1"/&gt;&lt;/event&gt;&lt;/events&gt;"""
        """</atom:content></atom:entry></atom>""")

        self.mox.StubOutWithMock(httplib2.Http, 'request')
        httplib2.Http.request('http://127.0.0.1:9000/test/%(event_type)s',
                              'POST', body=cuf_xml_body,
                              headers={'Content-Type': 'application/atom+xml'}
        ).AndReturn((MockResponse(201), None))
        self.mox.StubOutWithMock(uuid, 'uuid4')
        for i in range(0,3):
            uuid.uuid4().AndReturn("a70508f3-7254-4abc-9e14-49de6bb4d628")
        self.mox.ReplayAll()

        self.handler.handle_messages(messages, dict())

        self.mox.VerifyAll()

    def test_notify_fails(self):
        messages = [MockMessage(
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
                     'dummy_flavor_field_name': '40',
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
                'event_type': 'compute.instance.exists',
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
                     'dummy_flavor_field_name': '40',
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

