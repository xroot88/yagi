from unittest import TestCase
from yagi.handler.notification_options import NotificationOptions


class TestNotificationOptions(TestCase):
    def test_for_no_options(self):
        notification_options = NotificationOptions({'com.rackspace__1__options': '0'})
        options_dict = notification_options.to_cuf_options()
        self.assertEquals(options_dict, '')

    def test_for_red_hat(self):
        notification_options = NotificationOptions({'com.rackspace__1__options': '1'})
        options_dict = notification_options.to_cuf_options()
        self.assertEquals(options_dict, ' isRedHat="true"')

    def test_for_se_linux(self):
        notification_options = NotificationOptions({'com.rackspace__1__options': '2'})
        options_dict = notification_options.to_cuf_options()
        self.assertEquals(options_dict, ' isSELinux="true"')

    def test_for_windows(self):
        notification_options = NotificationOptions({'com.rackspace__1__options': '4'})
        options_dict = notification_options.to_cuf_options()
        self.assertEquals(options_dict, ' isWindows="true"')

    def test_for_windows_ms_sql(self):
        notification_options = NotificationOptions({'com.rackspace__1__options': '12'})
        options_dict = notification_options.to_cuf_options()
        self.assertEquals(options_dict, ' isWindows="true" isMSSQL="true"')

    def test_for_windows_ms_sql__web(self):
        notification_options = NotificationOptions({'com.rackspace__1__options': '36'})
        options_dict = notification_options.to_cuf_options()
        self.assertEquals(options_dict, ' isWindows="true" isMSSQLWeb="true"')
