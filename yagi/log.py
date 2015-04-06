import logging
from logging.handlers import WatchedFileHandler
from logging.config import fileConfig

import yagi.config

logger = logging

with yagi.config.defaults_for('logging') as default:
    default('logfile', 'yagi.log')
    default('default_level', 'INFO')
    default('logger', 'logging')
    default("config_file", "")

FORMAT = "%(name)s[%(levelname)s at %(asctime)s line: %(lineno)d] "\
         "%(message)s"


class YagiLogger(logging.Logger):
    def __init__(self, name, level=None):
        formatter = logging.Formatter(FORMAT)
        logging.Logger.__init__(self, name,
            logging.getLevelName(yagi.config.get('logging', 'default_level')))
        handlers = []
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        handlers.append(stream_handler)
        logfile = yagi.config.get('logging', 'logfile')
        if logfile:
            file_handler = WatchedFileHandler(filename=logfile)
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
        for handler in handlers:
            logging.Logger.addHandler(self, handler)


def setup_logging():
    config_file = yagi.config.get('logging', 'config_file')
    logfile = yagi.config.get('logging', 'logfile')
    default_log_level = logging.getLevelName(yagi.config.get('logging', 'default_level'))

    # This is a hack, but it's needed to pass the logfile name & default
    # loglevel into log handlers configured with a config file. (mdragon)
    logging.LOCAL_LOG_FILE = logfile
    logging.LOCAL_DEFAULT_LEVEL = default_log_level

    if config_file:
        #if a logging configfile exists, it overrides everything else.
        fileConfig(config_file)
    else:
        logging.root = YagiLogger("YagiLogger")
        logging.setLoggerClass(YagiLogger)
