import os
from yagi.handler.notification_options import NotificationOptions
from yagi.handler.notification_payload import NotificationPayload


class Notification(object):
    def __init__(self, message):
        self.message = message

    def _create_cuf_xml(self, deployment_info, json_body):
        payload = NotificationPayload(json_body['payload'])
        notification_options = {'com.rackspace__1__options': payload.options}
        cuf_xml_values = NotificationOptions(
            notification_options).to_cuf_options()
        cuf_xml_values['bandwidth_in'] = payload.bandwidth_in
        cuf_xml_values['bandwidth_out'] = payload.bandwidth_out
        cuf_xml_values['start_time'] = payload.start_time()
        cuf_xml_values['end_time'] = payload.end_time()
        cuf_xml_values['tenant_id'] = payload.tenant_id
        cuf_xml_values['instance_id'] = payload.instance_id
        cuf_xml_values['id'] = json_body['_unique_id']
        cuf_xml_values['flavor'] = payload.flavor
        cuf_xml_values['data_center'] = deployment_info['data_center']
        cuf_xml_values['region'] = deployment_info['region']
        script_dir = os.path.dirname(__file__)
        rel_path = "../templates/nova_cuf.xml"
        abs_file_path = os.path.join(script_dir, rel_path)
        f = open(abs_file_path)
        cuf_xml = f.read().format(**cuf_xml_values)
        return cuf_xml

    def convert_to_verified_message_in_cuf_format(self, deployment_info):
        cuf_xml= self._create_cuf_xml(deployment_info, self.message)
        verified_message = {}
        verified_message['payload'] = cuf_xml
        return verified_message
