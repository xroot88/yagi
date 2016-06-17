test_nova_xml_generator_values = {
    'tenant_id': 2882,
    'id': 'e53d007a-fc23-11e1-975c-cfa6b29bb814',
    'resource_id': '56',
    'resource_name': 'test',
    'data_center': 'DFW1',
    'region': 'DFW',
    'start_time':'2012-09-15T11:51:11Z',
    'end_time': '2012-09-16T11:51:11Z',
    'resource_type': 'SERVER',
    'options_string': 'osLicenseType="RHEL"',
    'bandwidth_in': 1001,
    'bandwidth_out': 19992,
    'flavor_id': 10,
    'flavor_name': "m1.nano",
    'status': "ACTIVE",
}

test_glance_xml_generator_values = {
    'tenant_id': 2882,
    'id': 'e53d007a-fc23-11e1-975c-cfa6b29bb814',
    'resource_id': '56',
    'data_center': 'DFW1',
    'region': 'DFW',
    'start_time':'2012-09-15T11:51:11Z',
    'end_time': '2012-09-16T11:51:11Z',
    'resource_type': 'SNAPSHOT',
    'storage': 12345,
    'server_id': 123,
    'server_name': 'X'
}

test_neutron_pub_ipv4_xml_generator_values = {
    'id': 'e1905c4e-4c6c-555a-af3a-92f8a03d2a99',
    'endTime': '2016-06-13T23:59:59Z',
    'resourceName': '10.69.221.27',
    'resourceId': '77777777-7777-7777-7777-777777777777',
    'startTime': '2016-06-13T00:00:00Z',
    'tenant_id': '404',
    'ipType': 'fixed',
    'resourceType': 'IP',
    'dataCenter': 'DFW1',
    'region': 'DFW',
    'tenantId': '404'
}

def verified_nova_message_in_cuf_format(values):
    vals = dict(**test_nova_xml_generator_values)
    vals.update(values)
    cuf_xml = ("""<event xmlns="http://docs.rackspace.com/core/event" """
    """xmlns:nova="http://docs.rackspace.com/event/nova" """
    """version="1" id="%(id)s" resourceId="%(resource_id)s" resourceName="%(resource_name)s" dataCenter="%(data_center)s" region="%(region)s" tenantId="%(tenant_id)s" """
    """startTime="%(start_time)s" endTime="%(end_time)s" type="USAGE">"""
    """<nova:product version="1" serviceCode="CloudServersOpenStack" """
    """resourceType="%(resource_type)s" flavorId="%(flavor_id)s" flavorName="%(flavor_name)s" status="%(status)s" """
    """%(options_string)s """
    """bandwidthIn="%(bandwidth_in)s" bandwidthOut="%(bandwidth_out)s"/>"""
    """</event>""") % vals
    return {'payload': cuf_xml}


def verified_glance_message_in_cuf_format(values):
    test_glance_xml_generator_values.update(values)
    cuf_xml = (
        """<event xmlns="http://docs.rackspace.com/core/event" """
        """xmlns:glance="http://docs.rackspace.com/event/glance" """
        """endTime="%(end_time)s" startTime="%(start_time)s" """
        """region="%(region)s" dataCenter="%(data_center)s" type="USAGE" """
        """id="%(id)s" resourceId="%(resource_id)s" """
        """tenantId="%(tenant_id)s" version="1">"""
        """<glance:product storage="1200" serverId="12309477" """
        """serviceCode="Glance" serverName="myServer" """
        """resourceType="BACKUP" version="1"/>"""
        """</event>""") % test_glance_xml_generator_values
    return {'payload': cuf_xml}


def verified_neutron_pub_ipv4_message_in_cuf_format(values):
    vals = dict(**test_neutron_pub_ipv4_xml_generator_values)
    vals.update(values)
    cuf_xml = (
        """<event xmlns="http://docs.rackspace.com/core/event" """
        """xmlns:neutron="http://docs.rackspace.com/usage/neutron/public-ip-usage" """
        """id="{id}" """
        """version="1" """
        """resourceId="{resourceId}" """
        """resourceName="{resourceName}" """
        """tenantId="{tenantId}" """
        """startTime="{startTime}" """
        """endTime="{endTime}" """
        """type="USAGE" """
        """dataCenter="{dataCenter}" """
        """region="{region}"> """
        """<neutron:product serviceCode="CloudNetworks" """
        """resourceType="{resourceType}" """
        """ipType="{ipType}"/> """
        """</event>"""
    )
    return {'payload': cuf_xml.format(**test_neutron_pub_ipv4_xml_generator_values)}
