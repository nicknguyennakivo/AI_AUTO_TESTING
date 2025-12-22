import logging
import os

import requests

from app import Config
from app.decorators.client import logging_requests, attempts, generate_random_smart_proxy, generate_random_proxy

request_timeout = 60
max_attempts = 10

logger = logging.getLogger(Config.APP_NAME)


class Client:
    def __init__(self, is_smart: bool = False):
        self.__session = requests.session()
        self.is_smart = is_smart
        self.set_proxy()

    def set_proxy(self):
        if self.is_smart:
            self.__set_smart_proxies()
        else:
            if int(os.getenv('PROXY_ENABLE', 0)):
                self.__set_proxies()

    @property
    def base_headers(self):
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
            "Accept": "application/xml, text/xml, */*; q=0.01",
            "Accept-Language": "en-US;q=0.5,en;q=0.3",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }

    @logging_requests
    @attempts
    def post(self, url: str, data: dict = None, **kwargs):
        kwargs["headers"] = self.__get_headers(kwargs.get("headers", {}))
        return self.__make_request("post", **{"url": url, "data": data, **kwargs})

    @logging_requests
    @attempts
    def get(self, url: str, **kwargs):
        if kwargs.get("retry", {}):
            logger.debug("Change PROXY")
            self.set_proxy()

        kwargs["headers"] = self.__get_headers(kwargs.get("headers", {}))
        return self.__make_request("get", **{"url": url, **kwargs})

    def __make_request(self, method: str, **kwargs):
        kwargs.pop('retry')
        kwargs.setdefault("timeout", request_timeout)

        if method == "post":
            return self.__session.post(**kwargs, verify=False)
        elif method == "get":
            return self.__session.get(**kwargs, verify=False)

    def __get_headers(self, additional: dict) -> dict:
        base = self.base_headers
        if additional:
            base.update(additional)

        return base

    @generate_random_proxy
    def __set_proxies(self, proxy):
        self.proxy = proxy
        logger.debug("USE PROXY - %s" % self.proxy)
        self.__session.proxies = {"https": self.proxy, "http": self.proxy}

    @generate_random_smart_proxy
    def __set_smart_proxies(self, proxy):
        logger.debug("USE PROXY - %s" % proxy)
        self.__session.proxies = {"https": proxy, "http": proxy}
