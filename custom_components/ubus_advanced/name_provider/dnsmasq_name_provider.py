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
from ..model import Name
from ..ubus_client import UbusClient
from .base_name_provider import BaseNameProvider

class DnsmasqNameProvider(BaseNameProvider):
    def __init__(self, logger: Logger, ubus_client: UbusClient):
        self._logger = logger.getChild('DnsmasqNameProvider')
        self._ubus_client = ubus_client

    def get(self) -> list[Name]:
        self._logger.debug('Loading data')
        return self._get_names()

    def _get_names(self) -> list[Name]:
        self._logger.debug('Getting DHCP names')
        dnsmasqs = self._ubus_client.call('uci', 'get', config='dhcp', type='dnsmasq')['values']

        names = []
        for dnsmasq in dnsmasqs:
            leasefile = dnsmasqs[dnsmasq].get('leasefile')
            if leasefile is None:
                self._logger.debug(f'Dnsmasq {dnsmasq} does not have a leasefile, ignoring')
                continue

            self._logger.debug(f'Reading {leasefile} lease file')
            leases = self._ubus_client.call('file', 'read', path=leasefile)
            if leases is None:
                self._logger.debug(f'Lease file {leasefile} not found')
                continue

            for lease in leases['data'].splitlines():
                _, mac, _, name, _ = lease.split(' ')
                names.append(Name(mac.upper(), name))

        self._logger.debug(f'Got {names} DHCP names')
        return names
