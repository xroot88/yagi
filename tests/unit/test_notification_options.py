from unittest import TestCase
from yagi.handler.notification_options import NotificationOptions


class TestNotificationOptions(TestCase):
    def test_for_no_options_gives_osLicense_linux(self):
        notification_options = NotificationOptions(
            {'com.rackspace__1__options': '0'})
        options_dict = notification_options.to_cuf_options()
        self.assertEquals(options_dict, 'osLicenseType="LINUX"')

    def test_for_red_hat(self):
        notification_options = NotificationOptions(
            {'com.rackspace__1__options': '1'})
        options_dict = notification_options.to_cuf_options()
        self.assertEquals(options_dict, 'osLicenseType="RHEL"')

    def test_for_se_linux(self):
        notification_options = NotificationOptions(
            {'com.rackspace__1__options': '2'})
        options_dict = notification_options.to_cuf_options()
        self.assertEquals(options_dict, '')

    def test_for_windows(self):
        notification_options = NotificationOptions(
            {'com.rackspace__1__options': '4'})
        options_dict = notification_options.to_cuf_options()
        self.assertEquals(options_dict, 'osLicenseType="WINDOWS"')

    def test_for_windows_ms_sql(self):
        notification_options = NotificationOptions(
            {'com.rackspace__1__options': '12'})
        options_dict = notification_options.to_cuf_options()
        self.assertEquals(options_dict,
                          'osLicenseType="WINDOWS" applicationLicense="MSSQL"')

    def test_for_windows_ms_sql__web(self):
        notification_options = NotificationOptions(
            {'com.rackspace__1__options': '36'})
        options_dict = notification_options.to_cuf_options()
        self.assertEquals(options_dict,
                          'osLicenseType="WINDOWS" '
                          'applicationLicense="MSSQL_WEB"')
