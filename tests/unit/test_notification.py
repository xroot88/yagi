from unittest import TestCase
import uuid
import mox
from tests.unit import utils
from yagi.handler.cuf_pub_handler import Notification
from yagi.handler.notification_payload import NotificationPayload


class TestNotification(TestCase):

    def setUp(self):
        self.mox = mox.Mox()

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_convert_to_cuf_format_when_launched_at_before_audit_period(self):
        exists_message = {
                'event_type': 'test',
                'message_id': 'some_uuid',
                '_unique_id': 'e53d007a-fc23-11e1-975c-cfa6b29bb814',
                'payload':
                    {'tenant_id':'2882',
                     'access_ip_v4': '5.79.20.138',
                     'access_ip_v6': '2a00:1a48:7804:0110:a8a0:fa07:ff08:157a',
                     'audit_period_beginning': '2012-09-15 11:51:11',
                     'audit_period_ending': '2012-09-16 11:51:11',
                     'bandwidth': {'private': {'bw_in': 0, 'bw_out': 264902},
                                   'public': {'bw_in': 1001,'bw_out': 19992}
                                  },
                     'image_meta': {'com.rackspace__1__options': '1'},
                     'instance_id': '56',
                     'instance_type_id': '10',
                     'launched_at': '2012-09-14 11:51:11',
                     'deleted_at': ''
                    }
            }
        self.mox.StubOutWithMock(uuid, 'uuid4')
        uuid.uuid4().AndReturn('some_other_uuid')
        self.mox.ReplayAll()
        values = utils.test_xml_generator_values
        values.update({'end_time': '2012-09-16 11:51:11'})
        expected_cuf_xml = utils.generate_verified_message_in_cuf_format(
            values)

        notification = Notification(exists_message)
        verified_message = notification.\
            convert_to_verified_message_in_cuf_format(
            {'region':'DFW','data_center':'DFW1'})

        self.assertEquals(expected_cuf_xml['payload'],
                          verified_message['payload'])

    def test_convert_to_cuf_format_when_launched_at_in_audit_period(self):
        audit_period_beginning = '2012-09-15 10:51:11'
        audit_period_ending = '2012-09-16 10:51:11'
        launched_at = '2012-09-15 11:51:11'
        exists_message = {
                'event_type': 'test',
                'message_id': 'some_uuid',
                '_unique_id': 'e53d007a-fc23-11e1-975c-cfa6b29bb814',
                'payload':
                    {'tenant_id':'2882',
                     'access_ip_v4': '5.79.20.138',
                     'access_ip_v6': '2a00:1a48:7804:0110:a8a0:fa07:ff08:157a',
                     'audit_period_beginning': audit_period_beginning,
                     'audit_period_ending': audit_period_ending,
                     'bandwidth': {'private': {'bw_in': 0, 'bw_out': 264902},
                                   'public': {'bw_in': 1001,'bw_out': 19992}
                                  },
                     'image_meta': {'com.rackspace__1__options': '1'},
                     'instance_id': '56',
                     'instance_type_id': '10',
                     'launched_at': launched_at,
                     'deleted_at': ''
                    }
            }
        self.mox.StubOutWithMock(uuid, 'uuid4')
        uuid.uuid4().AndReturn('some_other_uuid')
        self.mox.ReplayAll()
        values = utils.test_xml_generator_values
        values.update({'end_time': '2012-09-16 10:51:11'})
        expected_cuf_xml = utils.generate_verified_message_in_cuf_format(
            values)
        notification = Notification(exists_message)
        verified_message = \
            notification.convert_to_verified_message_in_cuf_format(
                {'region':'DFW','data_center':'DFW1'})

        self.assertEquals(expected_cuf_xml['payload'],
                          verified_message['payload'])

    def test_convert_to_cuf_format_when_deleted_at_in_audit_period(self):
        audit_period_beginning = '2012-09-15 10:51:11'
        audit_period_ending = '2012-09-16 10:51:11'
        launched_at = '2012-09-15 11:51:11'
        deleted_at = '2012-09-15 09:51:11'
        exists_message = {
                'event_type': 'test',
                'message_id': 'some_uuid',
                '_unique_id': 'e53d007a-fc23-11e1-975c-cfa6b29bb814',
                'payload':
                    {'tenant_id':'2882',
                     'access_ip_v4': '5.79.20.138',
                     'access_ip_v6': '2a00:1a48:7804:0110:a8a0:fa07:ff08:157a',
                     'audit_period_beginning': audit_period_beginning,
                     'audit_period_ending': audit_period_ending,
                     'bandwidth': {'private': {'bw_in': 0, 'bw_out': 264902},
                                   'public': {'bw_in': 1001,'bw_out': 19992}
                                  },
                     'image_meta': {'com.rackspace__1__options': '1'},
                     'instance_id': '56',
                     'instance_type_id': '10',
                     'launched_at': launched_at,
                     'deleted_at': deleted_at
                    }
            }
        values = utils.test_xml_generator_values
        values.update({'end_time': '2012-09-15 09:51:11'})
        self.mox.StubOutWithMock(uuid, 'uuid4')
        uuid.uuid4().AndReturn('some_other_uuid')
        expected_cuf_xml = utils.generate_verified_message_in_cuf_format(
            values)
        notification = Notification(exists_message)
        self.mox.ReplayAll()
        verified_message = notification.\
            convert_to_verified_message_in_cuf_format(
            {'region': 'DFW', 'data_center': 'DFW1'})

        self.assertEquals(expected_cuf_xml['payload'],
                          verified_message['payload'])


class TestNotificationPayload(TestCase):
    def test_start_time_should_get_max_of_launched_at_and_audit_period_beginning(self):
        payload_json ={'tenant_id':'2882',
                     'access_ip_v4': '5.79.20.138',
                     'access_ip_v6': '2a00:1a48:7804:0110:a8a0:fa07:ff08:157a',
                     'audit_period_beginning': '2012-09-15 10:51:11',
                     'audit_period_ending': '2012-09-16 10:51:11',
                     'bandwidth': {'private': {'bw_in': 0, 'bw_out': 264902},
                                   'public': {'bw_in': 1001,'bw_out': 19992}
                                  },
                     'image_meta': {'com.rackspace__1__options': '1'},
                     'instance_id': '56',
                     'instance_type_id': '10',
                     'launched_at': '2012-09-15 11:51:11',
                     'deleted_at': '2012-09-15 09:51:11'
                    }
        payload = NotificationPayload(payload_json)
        self.assertEquals(payload.start_time(), '2012-09-15 11:51:11')

    def test_end_time_should_get_min_of_deleted_at_and_audit_period_ending(self):
        payload_json ={'tenant_id':'2882',
                     'access_ip_v4': '5.79.20.138',
                     'access_ip_v6': '2a00:1a48:7804:0110:a8a0:fa07:ff08:157a',
                     'audit_period_beginning': '2012-09-15 10:51:11',
                     'audit_period_ending': '2012-09-16 10:51:11',
                     'bandwidth': {'private': {'bw_in': 0, 'bw_out': 264902},
                                   'public': {'bw_in': 1001,'bw_out': 19992}
                                  },
                     'image_meta': {'com.rackspace__1__options': '1'},
                     'instance_id': '56',
                     'instance_type_id': '10',
                     'launched_at': '2012-09-15 11:51:11',
                     'deleted_at': '2012-09-15 09:51:11'
                    }
        payload = NotificationPayload(payload_json)
        self.assertEquals(payload.end_time(), '2012-09-15 09:51:11')

    def test_end_time_should_be_audit_period_ending_when_deleted_at_is_empty(self):
        payload_json ={'tenant_id':'2882',
                     'access_ip_v4': '5.79.20.138',
                     'access_ip_v6': '2a00:1a48:7804:0110:a8a0:fa07:ff08:157a',
                     'audit_period_beginning': '2012-09-15 10:51:11',
                     'audit_period_ending': '2012-09-16 10:51:11',
                     'bandwidth': {'private': {'bw_in': 0, 'bw_out': 264902},
                                   'public': {'bw_in': 1001,'bw_out': 19992}
                                  },
                     'image_meta': {'com.rackspace__1__options': '1'},
                     'instance_id': '56',
                     'instance_type_id': '10',
                     'launched_at': '2012-09-15 11:51:11',
                     'deleted_at': ''
                    }
        payload = NotificationPayload(payload_json)
        self.assertEquals(payload.end_time(), '2012-09-16 10:51:11')

    def test_different_time_formats_should_not_raise_exception(self):
        payload_json ={'tenant_id':'2882',
                     'access_ip_v4': '5.79.20.138',
                     'access_ip_v6': '2a00:1a48:7804:0110:a8a0:fa07:ff08:157a',
                     'audit_period_beginning': '2012-09-15T10:51:11Z',
                     'audit_period_ending': '2012-09-16 10:51:11',
                     'audit_period_ending': '2012-09-16T10:51:11.799674',
                     'bandwidth': {'private': {'bw_in': 0, 'bw_out': 264902},
                                   'public': {'bw_in': 1001,'bw_out': 19992}
                                  },
                     'image_meta': {'com.rackspace__1__options': '1'},
                     'instance_id': '56',
                     'instance_type_id': '10',
                     'launched_at': '2012-09-15 11:51:11',
                     'deleted_at': ''
                    }
        payload = NotificationPayload(payload_json)
        self.assertEquals(payload.end_time(), '2012-09-16 10:51:11.799674')

