from unittest import TestCase
import uuid
import datetime
import mox
from tests.unit import utils
from yagi.handler import notification_payload
from yagi.handler.notification import NeutronPubIPv4UsageNotification
from yagi.handler.notification_payload import NeutronPubIPv4UsageNotificationPayload
import yagi.config
from yagi.handler.notification import neutron_pub_ipv4_v1_cuf_template


class TestNeutronPubIPv4Notification(TestCase):

    def setUp(self):
        self.event_type = 'ip.exists.verified.cuf'
        self.region = "DFW"
        self.data_center = "DFW1"

    def test_convert_to_cuf_deterministic_id(self):
        '''tests end to end generation of a cuf xml notification'''
        # this is a precalculated id from _uniq_id below
        det_id = 'e1905c4e-4c6c-555a-af3a-92f8a03d2a99'
        exists_message = {
            'event_type': 'ip.exists',
            'message_id': '33333333-3333-3333-3333-333333333333',
            '_unique_id': '99999999-9999-9999-9999-999999999999',
            'payload': {
                'endTime': '2016-06-13T23:59:59Z',
                'id': '77777777-7777-7777-7777-777777777777',
                'ip_address': '10.69.221.27',
                'ip_type': 'fixed',
                'startTime': '2016-06-13T00:00:00Z',
                'tenant_id': '404'
            }
        }
        changed_values = dict(id=det_id)
        expected_cuf_xml = \
                utils.verified_neutron_pub_ipv4_message_in_cuf_format(changed_values)

        notification = NeutronPubIPv4UsageNotification(exists_message,
                                    event_type=self.event_type,
                                    region=self.region,
                                    data_center=self.data_center)
        verified_message = notification.\
            convert_to_verified_message_in_cuf_format()

        self.assertEquals(expected_cuf_xml['payload'],
                          verified_message['payload'])
