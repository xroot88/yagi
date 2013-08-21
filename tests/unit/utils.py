test_xml_generator_values = {'tenant_id': 2882,
                             'id': 'e53d007a-fc23-11e1-975c-cfa6b29bb814',
                             'resource_id': '56',
                             'data_center': 'DFW1',
                             'region': 'DFW',
                             'start_time':'2012-09-15 11:51:11',
                             'end_time': '2012-09-16 11:51:11',
                             'resource_type': 'SERVER',
                             'is_red_hat': 'true', 'is_ms_sql': 'false',
                             'is_ms_sql_web': 'false', 'is_windows': 'false',
                             'is_se_linux': 'false', 'is_managed': 'false',
                             'bandwidth_in': 1001,
                             'bandwidth_out': 19992,
                             'flavor': 10}


def generate_verified_message_in_cuf_format(values):
    test_xml_generator_values.update(values)
    cuf_xml =("""<event xmlns="http://docs.rackspace.com/core/event" """
    """xmlns:nova="http://docs.rackspace.com/event/nova" """
    """version="1" tenantId="%(tenant_id)s" """
    """id="%(id)s" resourceId="%(resource_id)s" type="USAGE" """
    """dataCenter="%(data_center)s" region="%(region)s" """
    """startTime="%(start_time)s" endTime="%(end_time)s">"""
    """<nova:product version="1" serviceCode="CloudServersOpenStack" """
    """resourceType="%(resource_type)s" flavor="%(flavor)s" """
    """isRedHat="%(is_red_hat)s" isMSSQL="%(is_ms_sql)s" """
    """isMSSQLWeb="%(is_ms_sql_web)s" isWindows="%(is_windows)s" """
    """isSELinux="%(is_se_linux)s" isManaged="%(is_managed)s" """
    """bandwidthIn="%(bandwidth_in)s" bandwidthOut="%(bandwidth_out)s"/>"""
    """</event>""") % test_xml_generator_values
    message = {}
    message['payload'] = cuf_xml
    return message

