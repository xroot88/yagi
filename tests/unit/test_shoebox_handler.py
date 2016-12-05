import mock
import json
import unittest

from yagi import config

from yagi.handler import shoebox_handler


class Fake(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class TestShoeboxHandler(unittest.TestCase):
    def test_init(self):
        config.config = mock.MagicMock()
        config.config.items.return_value = ()
        sh = shoebox_handler.ShoeboxHandler()

        self.assertTrue(sh.roll_checker is None)
        self.assertEqual(sh.working_directory, '.')
        self.assertEqual(sh.destination_folder, '.')
        self.assertTrue(sh.roll_manager is not None)

    def test_init_full(self):
        config.config = mock.MagicMock()
        config.config.items.return_value = {
            'roll_checker': 'tests.unit.test_shoebox_handler:Fake',
            'working_directory': 'foo',
            'destination_folder': 'blah',
            'filename_template': 'mytemplate',
            'callback': 'tests.unit.test_shoebox_handler:Fake',
            'roll_manager': 'tests.unit.test_shoebox_handler:Fake',
        }.items()
        with mock.patch.object(shoebox_handler.os.path, "isdir") as isdir:
            isdir.return_value = True
            sh = shoebox_handler.ShoeboxHandler()
            self.assertTrue(sh.roll_checker is not None)
            self.assertEqual(sh.working_directory, 'foo')
            self.assertEqual(sh.destination_folder, 'blah')
            self.assertTrue(sh.roll_manager is not None)

    def test_json_roll_manager(self):
        config.config = mock.MagicMock()
        config.config.items.return_value = {
                'working_directory': 'foo',
                'roll_manager':
                    'shoebox.roll_manager:WritingJSONRollManager'}.items()
        with mock.patch.object(shoebox_handler.os.path, "isdir") as isdir:
            isdir.return_value = True
            with mock.patch("shoebox.roll_manager.WritingJSONRollManager"
                            "._archive_working_files") as awf:
                sh = shoebox_handler.ShoeboxHandler()
                self.assertTrue(sh.roll_manager is not None)
                self.assertEquals(sh.roll_manager.directory, 'foo')

    def test_wrapping_payload(self):
        config.config = mock.MagicMock()
        config.config.items.return_value = {
                'wrap_payload_with_region': 'True',
                'wrap_region': 'my_region',
                'wrap_cell': 'my_cell'}.items()
        with mock.patch.object(shoebox_handler.os.path, "isdir") as isdir:
            isdir.return_value = True
            with mock.patch("shoebox.roll_manager.WritingJSONRollManager"
                            "._archive_working_files") as awf:
                sh = shoebox_handler.ShoeboxHandler()
                self.assertTrue(sh.wrap_payload_with_region)
                self.assertEquals(sh.region, 'my_region')
                self.assertEquals(sh.cell, 'my_cell')
                fake_rm = mock.MagicMock()
                sh.roll_manager = fake_rm
                payload = {'event_type': 'test.thing',
                           'message_id': '1234-5678'}
                message = mock.MagicMock(payload=payload)
                sh.handle_messages([message], {})
                wrapped = {"region": "my_region",
                          "cell": "my_cell",
                          "notification": payload}
                jsoned = json.dumps(wrapped)
                fake_rm.write.assert_called_with({}, jsoned)
