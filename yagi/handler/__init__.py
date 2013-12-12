from ConfigParser import NoSectionError, NoOptionError
import yagi.config
import yagi.log

LOG = yagi.log.logger


class BaseHandler(object):
    CONFIG_SECTION = "DEFAULT"
    AUTO_ACK = False

    def __init__(self, app=None, queue_name=None):
        self.app = app
        self.queue_name = queue_name

    def config_get(self, key, default=None):
        return self._config_get(yagi.config.get, key, default=default)

    def config_getbool(self, key, default=None):
        return self._config_get(yagi.config.get_bool, key, default=default)

    def _config_get(self, method, key, default=None):
        val = None
        if self.queue_name is not None:
            try:
                val = method("%s:%s" % (self.CONFIG_SECTION, self.queue_name),
                             key)
            except NoSectionError:
                pass  # nothing here, try elsewhere.
        if val is None:
            val = method(self.CONFIG_SECTION, key, default=default)
        return val

    def filter_message(self, messages):
        try:
            filter_event_type_list = []
            exclude_filter_event_type_list = []
            filter_event_type = yagi.config.get(
                'filters', self.CONFIG_SECTION)
            if filter_event_type:
                filter_event_type_list = [a.strip() for a in filter_event_type.
                                          split(",")]
            exclude_filter_event_type = yagi.config.get(
                'exclude_filters', self.CONFIG_SECTION)
            if exclude_filter_event_type:
                exclude_filter_event_type_list = [a.strip() for a in
                                                  exclude_filter_event_type.
                                                  split(",")]
            if filter_event_type:
                messages = [message for message in messages if message.payload[
                            'event_type'] in filter_event_type_list]
            if exclude_filter_event_type:
                return [message for message in messages if message.payload[
                        'event_type'] not in exclude_filter_event_type_list]
        except (NoOptionError, NoSectionError):
            pass
        return messages

    def __call__(self, messages, env=None):
        if env is None:
            env = dict()
        if self.app:
            self.app(messages, env=env)
        filtered_messages = self.filter_message(messages)
        self.handle_messages(filtered_messages, env=env)
        return env

    def filter_payload(self, payload, env):
        filters = env.get('yagi.filters')
        if filters:
            for f in filters:
                payload = f(payload)
        return payload

    def iterate_payloads(self, messages, env):
        for message in messages:
            yield self.filter_payload(message.payload, env)
            if self.AUTO_ACK and not message.acknowledged:
                message.ack()

    def handle_messages(self, messages, env):
        raise NotImplementedError()
