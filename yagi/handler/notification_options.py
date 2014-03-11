class NotificationOptions(object):

    def __init__(self, options):
        self.options_bit_field = options['com.rackspace__1__options']

    def to_cuf_options(self):
        options_bit_to_dict_map = {'0':  ['LINUX'],
                                   '1':  ['RHEL'],  #RedHat
                                   '2':  [],  # SELinux not used
                                   '4':  ['WINDOWS'],
                                   '12': ['WINDOWS', 'MSSQL'],
                                   '36': ['WINDOWS', 'MSSQL_WEB'],
                                   '64': ['VYATTA']}
        options = options_bit_to_dict_map[self.options_bit_field]

        final_string = ""
        if len(options) >= 1:
            attribute_value = 'osLicenseType="%s"' % options[0]

            final_string += attribute_value
        if len(options) == 2:
            attribute_value = ' applicationLicense="%s"' % options[1]
            final_string += attribute_value
        return final_string