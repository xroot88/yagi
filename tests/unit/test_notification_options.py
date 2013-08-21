from unittest import TestCase
from yagi.handler.notification_options import NotificationOptions


class TestNotificationOptions(TestCase):
    def test_for_red_hat(self):
        options_dict_result = {'is_redhat': 'true', 'is_ms_sql': 'false',
                               'is_ms_sql_web': 'false', 'is_windows': 'false',
                               'is_se_linux': 'false', 'is_managed': 'false'}
        notification_options = NotificationOptions({'com.rackspace__1__options': '1'})
        options_dict = notification_options.to_cuf_options()
        self.assertEquals(options_dict,options_dict_result)

    def test_for_se_linux(self):
        options_dict_result = {'is_redhat': 'false', 'is_ms_sql': 'false',
                               'is_ms_sql_web': 'false', 'is_windows': 'false',
                               'is_se_linux': 'true', 'is_managed': 'false'}
        notification_options = NotificationOptions({'com.rackspace__1__options': '2'})
        options_dict = notification_options.to_cuf_options()
        self.assertEquals(options_dict,options_dict_result)

    def test_for_windows(self):
        options_dict_result = {'is_redhat': 'false', 'is_ms_sql': 'false',
                               'is_ms_sql_web': 'false', 'is_windows': 'true',
                               'is_se_linux': 'false', 'is_managed': 'false'}
        notification_options = NotificationOptions({'com.rackspace__1__options': '4'})
        options_dict = notification_options.to_cuf_options()
        self.assertEquals(options_dict,options_dict_result)

    def test_for_windows_ms_sql(self):
        options_dict_result = {'is_redhat': 'false', 'is_ms_sql': 'true',
                               'is_ms_sql_web': 'false', 'is_windows': 'true',
                               'is_se_linux': 'false', 'is_managed': 'false'}
        notification_options = NotificationOptions({'com.rackspace__1__options': '12'})
        options_dict = notification_options.to_cuf_options()
        self.assertEquals(options_dict,options_dict_result)

    def test_for_windows_ms_sql__web(self):
        options_dict_result = {'is_redhat': 'false', 'is_ms_sql': 'false',
                               'is_ms_sql_web': 'true', 'is_windows': 'true',
                               'is_se_linux': 'false', 'is_managed': 'false'}
        notification_options = NotificationOptions({'com.rackspace__1__options': '36'})
        options_dict = notification_options.to_cuf_options()
        self.assertEquals(options_dict,options_dict_result)
