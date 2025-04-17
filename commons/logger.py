import re
import queue
import logging
from logging.handlers import QueueHandler, QueueListener
import sys

from commons.singleton import Singleton

LOG_FORMAT = "%(asctime)s [%(name)s] [%(levelname)s] - %(message)s"


class NotificationLogger(metaclass=Singleton):

    def __init__(self):
        self.flush_handlers()
        log_queue = queue.Queue()
        queue_handler = QueueHandler(log_queue)
        log_formatter = logging.Formatter(LOG_FORMAT)
        root = logging.getLogger()
        root.addHandler(queue_handler)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(log_formatter)
        queue_listener = QueueListener(log_queue, console_handler)
        queue_listener.start()

        self.logger = root
        self.set_level()

    def set_level(self, log_level="INFO"):
        if log_level == "DEBUG":
            self.logger.setLevel(logging.DEBUG)
        elif log_level == "INFO":
            self.logger.setLevel(logging.INFO)
        elif log_level == "WARNING":
            self.logger.setLevel(logging.WARNING)
        elif log_level == "NOTSET":
            self.logger.setLevel(logging.NOTSET)
        else:
            self.logger.setLevel(logging.INFO)

    def get_logger(self, name=None):
        return self.logger if not name else logging.getLogger(name)

    @staticmethod
    def flush_handlers():
        logger = logging.getLogger()
        handlers = logger.handlers

        for handler in handlers:
            handler.flush()
            handler.close()
            logger.removeHandler(handler)


class SensitiveFormatter(logging.Formatter):
    """Formatter that removes sensitive information in logs."""

    @staticmethod
    def _filter(s):
        return re.sub(r" -p'[^' ]+'", r' -pxxxx', s)

    def format(self, record):
        original = logging.Formatter.format(self, record)
        return self._filter(original)
