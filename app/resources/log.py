import sys
import logging

from app.config import Config

logger = logging.getLogger(Config.APP_NAME)
logger.setLevel(logging.DEBUG)
logging.getLogger().handlers = []

globalExtra = {}


def addExtra(key, val=None):
    globalExtra[key] = val


def getExtra(extra=None):
    if extra is None:
        extra = {}
    extra.update(globalExtra)
    return extra


class LogFilter(logging.Filter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def filter(self, record):
        record.extra = getExtra()
        return True


def initLogger():
    if Config.LOGGER_TYPE == "file":
        fh = logging.FileHandler("app.log")
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        fh.setFormatter(formatter)
        fh.addFilter(LogFilter())
        logger.addHandler(fh)
    else:
        sh = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        sh.setFormatter(formatter)
        sh.addFilter(LogFilter())
        logger.addHandler(sh)
