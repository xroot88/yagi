import datetime
import logging
import uuid
import yagi

LOG = logging.getLogger(__name__)


def start_time(launched_at, audit_period_beginning):
        start_time = max(launched_at, audit_period_beginning)
        return format_time(start_time, return_in_datetime_format=True)


def end_time(deleted_at, audit_period_ending):
        if not deleted_at:
            return format_time(audit_period_ending, return_in_datetime_format=True)
        end_time = min(deleted_at, audit_period_ending)
        return format_time(end_time, return_in_datetime_format=True)


def format_time(time,return_in_datetime_format=False):
        if 'T' in time:
            try:
                # Old way of doing it
                time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f")
            except ValueError:
                try:
                    # Old way of doing it, no millis
                    time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S")
                except Exception, e:
                    LOG.exception("BAD DATE: %s", time)
        else:
            try:
                time = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                try:
                    time = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        time = datetime.datetime.strptime(time, "%d %m %Y %H:%M:%S")
                    except Exception, e:
                        LOG.exception("BAD DATE: %s", time)
        if return_in_datetime_format:
            return time
        return str(time)


class NotificationPayload(object):
    def __init__(self, payload_json):
        self.deleted_at = ''
        self.image_meta = payload_json.get('image_meta', {})
        self.options = self.image_meta.get('com.rackspace__1__options', '0')
        bandwidth = payload_json.get('bandwidth', {})
        public_bandwidth = bandwidth.get('public', {})
        self.bandwidth_in = public_bandwidth.get('bw_in', 0)
        self.bandwidth_out = public_bandwidth.get('bw_out', 0)

        self.launched_at = str(format_time(payload_json['launched_at']))

        self.audit_period_beginning = str(format_time(
            payload_json['audit_period_beginning']))

        self.audit_period_ending = str(format_time(
            payload_json['audit_period_ending']))

        if payload_json['deleted_at']:
            self.deleted_at = str(format_time(
                payload_json['deleted_at']))

        self.tenant_id = payload_json.get('tenant_id', "")
        self.instance_id = payload_json.get('instance_id', "")
        self.instance_name = payload_json.get('display_name', "")
        field_name = yagi.config.get('nova', 'nova_flavor_field_name')
        self.flavor_id = payload_json[field_name]
        self.flavor_name = payload_json['instance_type']
        task_state = payload_json.get('state_description', "")
        vm_state = payload_json.get('state', "")
        self.status = self._get_status(task_state, vm_state)
        self.start_time = start_time(self.launched_at,
                                     self.audit_period_beginning)
        self.end_time = end_time(self.deleted_at, self.audit_period_ending)

    def _get_status(self, task_state, vm_state):
        _STATE_MAP = {
            "active": {
                'default': 'ACTIVE',
                "rebooting": 'REBOOT',
                "rebooting_hard": 'HARD_REBOOT',
                "updating_password": 'PASSWORD',
                "rebuilding": 'REBUILD',
                "rebuild_block_device_mapping": 'REBUILD',
                "rebuild_spawning": 'REBUILD',
                "migrating": 'MIGRATING',
                "resize_prep": 'RESIZE',
                "resize_migrating": 'RESIZE',
                "resize_migrated": 'RESIZE',
                "resize_finish": 'RESIZE',
            },
            "building": {
                'default': 'BUILD',
            },
            "stopped": {
                'default': 'SHUTOFF',
            },
            "resized": {
                'default': 'VERIFY_RESIZE',
                "resize_reverting": 'REVERT_RESIZE',
            },
            "paused": {
                'default': 'PAUSED',
            },
            "suspended": {
                'default': 'SUSPENDED',
            },
            "rescued": {
                'default': 'RESCUE',
            },
            "error": {
                'default': 'ERROR',
            },
            "deleted": {
                'default': 'DELETED',
            },
            "soft-delete": {
                'default': 'SOFT_DELETED',
            },
            "shelved": {
                'default': 'SHELVED',
            },
            "shelved_offloaded": {
                'default': 'SHELVED_OFFLOADED',
            },
        }
        task_map = _STATE_MAP.get(vm_state, dict(default='UNKNOWN'))
        status = task_map.get(task_state, task_map['default'])
        if status == "UNKNOWN":
            LOG.error(("status is UNKNOWN from vm_state=%(vm_state)s "
                    "task_state=%(task_state)s. Bad upgrade or db "
                    "corrupted?"),
                  {'vm_state': vm_state, 'task_state': task_state})
        return status




class GlanceNotificationPayload(object):
    def __init__(self, payload_json, time_format):
        deleted_at = None
        self.images = []
        raw_images = payload_json.get('images', {})
        audit_period_beginning = payload_json.get('audit_period_beginning', "")
        audit_period_ending = payload_json.get('audit_period_ending', "")
        for raw_image in raw_images:
            image = {}
            image['id'] = uuid.uuid4()
            image['resource_id'] = raw_image.get('id', "")
            image['tenant_id'] = payload_json.get('owner', "")
            created_at = raw_image['created_at']
            if raw_image['deleted_at']:
                deleted_at = raw_image['deleted_at']
            image['start_time'] = datetime.datetime.strftime(start_time(
                created_at, audit_period_beginning), time_format)

            image['end_time'] = datetime.datetime.strftime(end_time(
                deleted_at, audit_period_ending), time_format)
            properties = raw_image.get('properties', {})
            image['resource_type'] = properties.get('image_type', "")
            image['server_id'] = properties.get('instance_uuid', "")
            image['server_name'] = properties.get('instance_name', "")
            image['storage'] = raw_image.get('size', "")
            self.images.append(image)
