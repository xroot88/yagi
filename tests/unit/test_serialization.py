import functools
import unittest
import xml.etree.ElementTree
import stubout

import yagi.config
import yagi.serializer
from yagi.serializer import atom

class SerializerTests(unittest.TestCase):
    def setUp(self):
        self.stubs = stubout.StubOutForTesting()
        self.test_event = {
            "event_type": "compute.instance.update",
            "timestamp": "2013-08-06 13:57:57.468516",
            "priority": "INFO",
            "publisher_id": "compute.test",
            "message_id": "46d55117-d2ff-4124-a184-5ff21a5c4c9b",
            "payload": {"state_description": "",
                        "availability_zone": None,
                        "ephemeral_gb": 0,
                        "instance_type_id": 6,
                        "bandwidth": {},
                        "deleted_at": "",
                        "reservation_id": "r-z2ckc2ds",
                        "memory_mb": 64,
                        "user_id": "2b0d6ab80bc6410e9694772cb344a309",
                        "hostname": "test2",
                        "state": "error",
                        "old_state": "error",
                        "old_task_state": "spawning",
                        "metadata": [],
                        "node": "compute.test",
                        "ramdisk_id": "01dff59f-a3eb-466c-b0c8-63712f586b06",
                        "access_ip_v6": None,
                        "access_ip_v4": None,
                        "disk_gb": 0,
                        "kernel_id": "61b7c758-9e9a-4381-bc24-70931e0f8786",
                        "host": "compute.test",
                        "display_name": "test2",
                        "image_ref_url": "http://127.0.0.1:9292/images/309019bb-742b-45f1-a809-e0be7c6123d0",
                        "audit_period_beginning": "2013-08-06T13:00:00.000000",
                        "audit_period_ending": "2013-08-06T13:57:57.465039",
                        "root_gb": 0,
                        "tenant_id": "71e7841cace54b80b1bc98af3cdfd7bc",
                        "created_at": "2013-08-06 13:57:49",
                        "launched_at": "",
                        "instance_id": "475283c0-2a2f-4ac1-b2c0-cc8e9a67310d",
                        "instance_type": "m1.nano",
                        "vcpus": 1,
                        "image_meta": {"kernel_id": "61b7c758-9e9a-4381-bc24-70931e0f8786",
                                       "ramdisk_id": "01dff59f-a3eb-466c-b0c8-63712f586b06",
                                       "base_image_ref": "309019bb-742b-45f1-a809-e0be7c6123d0"
                                       },
                        "architecture": None,
                        "new_task_state": None,
                        "os_type": None,
                        },
        }
        self.test_entity = dict(content=self.test_event,
                                id=self.test_event['message_id'],
                                event_type=self.test_event['event_type'])
        self.ns='{http://www.w3.org/2005/Atom}'

        config_dict = {
            'event_feed': {
                'feed_title': 'feed_title',
                'feed_host': 'feed_host',
                'use_https': False,
                'serializer_driver': 'yagi.serializer.atom',
                'port': 'port',
                'atom_categories': "Test, 123, The, Thing"
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

        self.stubs.Set(yagi.config, 'config_with', config_with)
        self.stubs.Set(yagi.config, 'get', get)

    def tearDown(self):
        self.stubs.UnsetAll()

    def test_no_link(self):
        body = atom.dump_item(self.test_entity, entity_links=False)
        xml_data = xml.etree.ElementTree.fromstring(body)
        links = xml_data.findall(self.ns+'link')
        self.assertEquals(len(links),0)

    def test_link(self):
        body = atom.dump_item(self.test_entity, entity_links=True)
        xml_data = xml.etree.ElementTree.fromstring(body)
        links = xml_data.findall(self.ns+'link')
        self.assertEquals(len(links),1)

    def test_entry_id(self):
        body = atom.dump_item(self.test_entity)
        xml_data = xml.etree.ElementTree.fromstring(body)
        ids = xml_data.findall(self.ns+'id')
        self.assertEquals(len(ids),1)
        id_tag = ids[0]
        self.assertEquals(id_tag.text, 'urn:uuid:46d55117-d2ff-4124-a184-5ff21a5c4c9b')

    def test_dump_item(self):
        body = atom.dump_item(self.test_entity)
        self.assertTrue(len(body) > 0)
        xml_data = xml.etree.ElementTree.fromstring(body)
        self.assertEquals(xml_data.tag, self.ns+'entry')

    def test_load_serializer(self):
        """Contrived test for basic functionality"""
        ser = yagi.serializer.feed_serializer()
        self.assertEqual(ser, yagi.serializer.atom)
