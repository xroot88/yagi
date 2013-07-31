from ConfigParser import NoSectionError
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
        filters = yagi.config.get('filters')
        if filters:
            filter_event_type = filters.get(self.CONFIG_SECTION)
            if filter_event_type:
                return [message for message in messages if
                    message.payload['event_type'] in filter_event_type]
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
