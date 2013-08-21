class NotificationOptions(object):

    def __init__(self, options):
        self.options_bit_field = options['com.rackspace__1__options']
        NotificationOptions._all_cuf_options = {
            'is_redhat': 'false', 'is_ms_sql': 'false',
            'is_ms_sql_web': 'false', 'is_windows': 'false',
            'is_se_linux': 'false', 'is_managed': 'false'}


    def to_cuf_options(self):
        options_bit_to_dict_map = {'1': {'is_redhat': 'true'},
                                   '2': {'is_se_linux': 'true'},
                                   '4': {'is_windows': 'true'},
                                   '12': {'is_windows': 'true',
                                          'is_ms_sql': 'true'},
                                   '36': {'is_windows': 'true',
                                          'is_ms_sql_web': 'true'}}
        NotificationOptions._all_cuf_options.update(
            options_bit_to_dict_map[self.options_bit_field])
        return NotificationOptions._all_cuf_options