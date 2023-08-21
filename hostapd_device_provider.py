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
import collections
from .device_provider import Device, DeviceProvider

DEVICE_PROVIDER_HOSTAPD = 'hostapd'

Network = collections.namedtuple('Network', ['hostapd', 'ssid'])

class HostapdDeviceProvider(DeviceProvider):
    def __init__(self, logger, ubus_client):
        self._logger = logger.getChild('HostapdDeviceProvider')
        self._ubus_client = ubus_client

    def get(self):
        self._logger.debug('Loading data')
        networks = self._get_networks()

        return self._get_devices(networks)

    def _get_networks(self):
        self._logger.debug('Getting Wi-Fi networks')
        hostapds = self._ubus_client.list('hostapd.*').keys()

        networks = []
        for hostapd in hostapds:
            self._logger.debug(f'Getting SSID of network {hostapd}')
            ssid = self._ubus_client.call(hostapd, 'get_status')['ssid']

            networks.append(Network(hostapd, ssid))

        self._logger.debug(f'Got {networks} Wi-Fi networks')
        return networks

    def _get_devices(self, networks):
        self._logger.debug('Getting devices')
        devices = []
        for network in networks:
            self._logger.debug(f'Getting {network.hostapd} network\'s clients')
            clients = self._ubus_client.call(network.hostapd, 'get_clients')['clients']
            for mac in clients:
                if not clients[mac]['authorized']:
                    self._logger.debug(f'Client {mac} not authorized, ignoring')
                    continue

                devices.append(Device(mac.upper(), network.ssid))

        self._logger.debug(f'Got {devices} devices')
        return devices
