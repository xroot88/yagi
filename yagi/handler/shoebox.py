from shoebox import roll_manager
import simport

import yagi.config
import yagi.handler
import yagi.log
import yagi.utils

LOG = yagi.log.logger


class ShoeboxHandler(yagi.handler.BaseHandler):
    """The shoebox handler doesn't really fit with
       yagi persistence interface currently. We'll need
       to refactor one or the other to clean it up.
    """

    def __init__(self, app=None, queue_name=None):
        super(ShoeboxHandler, self).__init_(app, queue_name)
        self.config = yagi.config.get("shoebox", {})
        self.roll_checker = simport.load('roll_checker')(**self.config)
        self.working_directory = self.config.get('working_directory', '.')
        template=self.config.get('filename_template',
                                 'events_%Y_%m_%d_%X_%f.dat')
        cb = simport.load(yagi.config.get('callback'))(config=self.config)
        self.roll_manager = roll_manager.WritingRollManager(template,
                                roll_checker, self.working_directory,
                                archive_callback=cb)

    def handle_messages(self, messages, env):
        # TODO(sandy): iterate_payloads filters messages first ... not
        # sure if we want that for raw archiving.
        for payload in self.iterate_payloads(messages, env):
            json_event = json.dumps(event,
                                    cls=notification_utils.DateTimeEncoder)

            manager.write(metadata, json_event)
