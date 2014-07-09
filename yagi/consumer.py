import datetime
import logging
import time

import yagi.config
import yagi.filters
import yagi.stats
import yagi.utils


LOG = logging.getLogger(__name__)


class Consumer(object):
    def __init__(self, queue_name, app=None, config=None):
        self.filters = []
        self.queue_name = queue_name
        self.config = yagi.config.config_with("consumer:%s" % queue_name)
        self.connect_time = None
        self.connection = None
        self.consumer = None
        apps = [a.strip() for a in self.config("apps").split(",")]
        prev_app = None
        for a in apps:
            prev_app = yagi.utils.import_class(a)(prev_app,
                                                queue_name=self.queue_name)
        self.app = prev_app
        self.max_messages = int(self.config("max_messages"))

        filter_names = self.config("filters")
        if filter_names:
            filters = (f.strip() for f in filter_names.split(","))
            for f in filters:
                section = yagi.config.config_with("filter:%s" % f)
                map_file = section("map_file")
                method = section("method")
                filter_class = yagi.filters.get_filter(method, map_file, LOG)
                if not filter_class:
                    # Since these should go away, I don't know that it's a big
                    # deal if we can't find one
                    continue
                self.filters.append(filter_class)

    def connect(self, connection, consumer):
        self.disconnect()
        self.connection = connection
        self.consumer = consumer
        self.connect_time = datetime.datetime.now()

    def disconnect(self):
        if self.connection:
            try:
                self.connection.close()
            except Exception, e:
                LOG.info("Error closing broker connection")
                LOG.exception(e)
        self.connection = None
        self.consumer = None

    def fetched_messages(self, messages):
        if self.filters:
            env = {'yagi.filters': self.filters}
        else:
            env = {}
        try:
            start_time = time.time()
            self.app(messages, env=env)
            yagi.stats.time_stat(yagi.stats.elapsed_message(),
                                 time.time() - start_time)
        except Exception, e:
            # If we get all the way back out here, that's bad juju
            LOG.exception("Error in fetched_messages: \n%s" % e)

        yagi.stats.increment_stat(yagi.stats.messages_sent(),
                                  len(messages))
