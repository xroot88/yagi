import os
import uuid
import datetime
from yagi.handler.notification_options import NotificationOptions
from yagi.handler.notification_payload import NotificationPayload, GlanceNotificationPayload

nova_cuf_template = ("""<event xmlns="http://docs.rackspace.com/core/event" """
"""xmlns:nova="http://docs.rackspace.com/event/nova" version="1" """
"""id="%(id)s" resourceId="%(instance_id)s" """
"""resourceName="%(instance_name)s" dataCenter="%(data_center)s" """
"""region="%(region)s" tenantId="%(tenant_id)s" startTime="%(start_time)s" """
"""endTime="%(end_time)s" type="USAGE"><nova:product version="1" """
"""serviceCode="CloudServersOpenStack" resourceType="SERVER" flavorId"""
"""="%(flavor_id)s" flavorName="%(flavor_name)s" status="%(status)s" """
"""%(options_string)s bandwidthIn="%(bandwidth_in)s" """
"""bandwidthOut="%(bandwidth_out)s"/></event>""")

glance_cuf_template_per_image = ("""<event endTime="%(end_time)s" """
"""startTime="%(start_time)s" region="%(region)s" """
"""dataCenter="%(data_center)s" type="USAGE" id="%(id)s" """
"""resourceId="%(resource_id)s" tenantId="%(tenant_id)s" version="1"> """
"""<glance:product storage="%(storage)s" serverId="%(server_id)s" """
"""serviceCode="Glance" serverName="%(server_name)s" """
"""resourceType="%(resource_type)s" version="1"/></event>""")

atom_hopper_time_format = "%Y-%m-%dT%H:%M:%SZ"


class Notification(object):
    def __init__(self, message):
        self.message = message

    def _create_cuf_xml(self, deployment_info, json_body):
        payload = NotificationPayload(json_body['payload'])
        notification_options = {'com.rackspace__1__options': payload.options}
        cuf_xml_values = {}
        cuf_xml_values['options_string'] = NotificationOptions(
            notification_options).to_cuf_options()
        cuf_xml_values['bandwidth_in'] = payload.bandwidth_in
        cuf_xml_values['bandwidth_out'] = payload.bandwidth_out
        cuf_xml_values['start_time'] = datetime.datetime.strftime(
            payload.start_time, atom_hopper_time_format)
        cuf_xml_values['end_time'] = datetime.datetime.strftime(
            payload.end_time, atom_hopper_time_format)
        cuf_xml_values['tenant_id'] = payload.tenant_id
        cuf_xml_values['instance_id'] = payload.instance_id
        cuf_xml_values['instance_name'] = payload.instance_name
        cuf_xml_values['id'] = uuid.uuid4()
        cuf_xml_values['flavor_id'] = payload.flavor_id
        cuf_xml_values['flavor_name'] = payload.flavor_name
        cuf_xml_values['status'] = payload.status
        cuf_xml_values['data_center'] = deployment_info['data_center']
        cuf_xml_values['region'] = deployment_info['region']
        cuf_xml = nova_cuf_template % cuf_xml_values
        return cuf_xml

    def convert_to_verified_message_in_cuf_format(self, deployment_info):
        cuf_xml = self._create_cuf_xml(deployment_info, self.message)
        return {'payload': cuf_xml}


class GlanceNotification(object):
    def __init__(self, message):
        self.message = message

    def _create_cuf_xml(self, deployment_info, json_body):
        payload = GlanceNotificationPayload(json_body['payload'], atom_hopper_time_format)
        images = payload.images
        cuf = "<events>"
        for image in images:
            image['data_center'] = deployment_info['data_center']
            image['region'] = deployment_info['region']
            cuf_xml = glance_cuf_template_per_image % image
            cuf += cuf_xml
        cuf += "</events>"
        return cuf

    def convert_to_verified_message_in_cuf_format(self, deployment_info):
        cuf_xml= self._create_cuf_xml(deployment_info, self.message)
        return {'payload': cuf_xml}