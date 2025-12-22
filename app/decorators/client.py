import logging
import os
import random
import urllib.parse
from functools import wraps
from http.client import RemoteDisconnected
from time import sleep

from requests.exceptions import ChunkedEncodingError, ProxyError, SSLError

from app import Config

logger = logging.getLogger(Config.APP_NAME)


class InstagramError(Exception):
    pass


def attempts(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        retry = False
        for i in range(10):
            try:
                response = f(*args, **dict(kwargs, retry=retry))

                if response.status_code == 401:
                    raise InstagramError

                return response
            except (
                InstagramError,
                ChunkedEncodingError,
                ProxyError,
                SSLError,
                RemoteDisconnected,
            ) as e:
                retry = True
                logger.exception(f"method: {f.__name__}, Error: {e}, retrying...")
            except Exception as e:
                retry = True
                logger.exception(
                    f"Exception method: {f.__name__}, Error: {e}, retrying..."
                )
                sleep(5)

        logger.exception("Exit")
        return False

    return wrapper


def logging_requests(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        response = f(*args, **kwargs)

        info = (
            "--------------------------------------------------------------------------------------------------\n"
            f"Request DATA:\n{args}, \n\n"
            f"Request DATA:\n{kwargs}, \n\n"
            f"Response DATA:\n"
            f"Code: {response.status_code}, \n"
            f"Headers: {response.headers}, \n"
            # f"Content: {response.text}, \n"
            "--------------------------------------------------------------------------------------------------\n"
        )
        if response.status_code != 200:
            logger.debug(info)

        return response

    return wrapper


def generate_random_smart_proxy(func):
    def wrapper(self):
        port = random.randint(10000, 10050)
        # port = 10000

        auth = "{}:{}@{}:{}".format(
            os.getenv("PROXY_USERNAME"),
            urllib.parse.quote_plus(os.getenv("PROXY_PASSWORD")),
            os.getenv("PROXY_HOST"),
            port,
        )
        proxy = "http://{}".format(auth)

        func(self, proxy)

    return wrapper

def generate_random_proxy(func):
    def wrapper(self):
        auth = "{}:{}@{}:{}".format(
            os.getenv("PROXY_USERNAME"),
            os.getenv("PROXY_PASSWORD"),
            os.getenv("PROXY_HOST"),
            os.getenv("PROXY_PORT"),
        )
        proxy = "http://{}".format(auth)

        func(self, proxy)

    return wrapper
