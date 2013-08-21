import datetime


class NotificationPayload(object):
    def __init__(self, payload_json):
        self.deleted_at = ''
        self.options = payload_json['image_meta']['com.rackspace__1__options']
        self.bandwidth_in = payload_json['bandwidth']['public']['bw_in']
        self.bandwidth_out = payload_json['bandwidth']['public']['bw_out']

        self.launched_at = str(self._format_time(payload_json['launched_at']))

        self.audit_period_beginning = str(self._format_time(
            payload_json['audit_period_beginning']))

        self.audit_period_ending = str(self._format_time(
            payload_json['audit_period_ending']))

        if payload_json['deleted_at']:
            self.deleted_at = str(self._format_time(
                payload_json['deleted_at']))

        self.tenant_id = payload_json['tenant_id']
        self.instance_id = payload_json['instance_id']
        self.flavor = payload_json['instance_type_id']

    def start_time(self):
        start_time = max(self.launched_at, self.audit_period_beginning)
        return self._format_time(start_time)

    def end_time(self):
        if not self.deleted_at:
            return self._format_time(self.audit_period_ending)
        end_time = min(self.deleted_at, self.audit_period_ending)
        return self._format_time(end_time)

    def _format_time(self,time):
        if 'T' in time:
            try:
                # Old way of doing it
                time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f")
            except ValueError:
                try:
                    # Old way of doing it, no millis
                    time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S")
                except Exception, e:
                    print "BAD DATE: ", e
        else:
            try:
                time = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                try:
                    time = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
                except Exception, e:
                    print "BAD DATE: ", e

        return str(time)