# Copyright © 2023 Michał Przybyś <michal@przybys.eu>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software
# and associated documentation files (the “Software”), to deal in the Software without
# restriction, including without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
# BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
from logging import Logger
from openwrt.ubus import Ubus
from openwrt.ubus.const import API_RPC_CALL, API_RPC_LIST
from typing import Any, Callable
from urllib.parse import urlunparse, urlparse

class UbusClient:
    def __init__(self, logger: Logger, host: str, username: str, password: str):
        self._logger = logger.getChild('UbusClient')

        host_parsed = urlparse(host)
        url = urlunparse((host_parsed.scheme, host_parsed.netloc, '/ubus', '', '', ''))

        self._ubus = Ubus(url, username, password, verify=True)

    def connect(self) -> None:
        self._logger.info(f'Connecting to ubus {self._ubus.host}')
        self._ubus.connect()

    def call(self, subsystem: str, method: str, **arguments: dict[str, Any]) -> dict[str, Any]:
        self._logger.debug(f'Calling method {method} from {subsystem} subsystem with {arguments}')
        return self._retry(lambda: self._ubus.api_call(API_RPC_CALL, subsystem, method, arguments))

    def list(self, subsystem: str) -> dict[str, Any]:
        self._logger.debug(f'Listing subsystem {subsystem}')
        return self._retry(lambda: self._ubus.api_call(API_RPC_LIST, subsystem))

    def _retry(self, callback: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        try:
            return callback()
        except PermissionError:
            self._logger.warning(f'Permission error, possible invalid session, reconnecting...')
            self.connect()
            return callback()
