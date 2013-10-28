class NotificationOptions(object):

    def __init__(self, options):
        self.options_bit_field = options['com.rackspace__1__options']

    def to_cuf_options(self):
        options_bit_to_dict_map = {'0': [],
                                   '1': ['isRedHat'],
                                   '2': ['isSELinux'],
                                   '4': ['isWindows'],
                                   '12': ['isWindows',
                                          'isMSSQL'],
                                   '36': ['isWindows',
                                          'isMSSQLWeb']}
        options = options_bit_to_dict_map[self.options_bit_field]
        final_string = ""
        for name in options:
                final_string += (' %s="true"' %name)
        return final_string