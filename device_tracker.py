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
import fnmatch
import homeassistant
import logging
import voluptuous
from .dnsmasq_name_provider import NAME_PROVIDER_DNSMASQ, DnsmasqNameProvider
from .hostapd_device_provider import DEVICE_PROVIDER_HOSTAPD, HostapdDeviceProvider
from .ubus_client import UbusClient

CONF_DEVICE_PROVIDER = 'device_provider'
CONF_NAME_PROVIDER = 'name_provider'
CONF_MAC_BLACKLIST = 'mac_blacklist'
CONF_MAC_WHITELIST = 'mac_whitelist'
CONF_NAME_BLACKLIST = 'name_blacklist'
CONF_NAME_WHITELIST = 'name_whitelist'
CONF_SSID_BLACKLIST = 'ssid_blacklist'
CONF_SSID_WHITELIST = 'ssid_whitelist'

DEVICE_PROVIDERS = [
    DEVICE_PROVIDER_HOSTAPD
]
NAME_PROVIDERS = [
    NAME_PROVIDER_DNSMASQ
]

PLATFORM_SCHEMA = homeassistant.components.device_tracker.PLATFORM_SCHEMA.extend(
    {
        voluptuous.Required(homeassistant.const.CONF_HOST): homeassistant.helpers.config_validation.url_no_path,
        voluptuous.Required(homeassistant.const.CONF_USERNAME): homeassistant.helpers.config_validation.string,
        voluptuous.Required(homeassistant.const.CONF_PASSWORD): homeassistant.helpers.config_validation.string,
        voluptuous.Optional(CONF_MAC_BLACKLIST, default=[]): voluptuous.All(homeassistant.helpers.config_validation.ensure_list, [homeassistant.helpers.config_validation.string, homeassistant.helpers.config_validation.matches_regex('^[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}$')]),
        voluptuous.Optional(CONF_MAC_WHITELIST, default=[]): voluptuous.All(homeassistant.helpers.config_validation.ensure_list, [homeassistant.helpers.config_validation.string, homeassistant.helpers.config_validation.matches_regex('^[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}$')]),
        voluptuous.Optional(CONF_NAME_BLACKLIST, default=[]): voluptuous.All(homeassistant.helpers.config_validation.ensure_list, [homeassistant.helpers.config_validation.string]),
        voluptuous.Optional(CONF_NAME_WHITELIST, default=[]): voluptuous.All(homeassistant.helpers.config_validation.ensure_list, [homeassistant.helpers.config_validation.string]),
        voluptuous.Optional(CONF_SSID_BLACKLIST, default=[]): voluptuous.All(homeassistant.helpers.config_validation.ensure_list, [homeassistant.helpers.config_validation.string, voluptuous.validators.Length(1, 32)]),
        voluptuous.Optional(CONF_SSID_WHITELIST, default=[]): voluptuous.All(homeassistant.helpers.config_validation.ensure_list, [homeassistant.helpers.config_validation.string, voluptuous.validators.Length(1, 32)]),
        voluptuous.Optional(CONF_DEVICE_PROVIDER, default=DEVICE_PROVIDER_HOSTAPD): voluptuous.In(DEVICE_PROVIDERS),
        voluptuous.Optional(CONF_NAME_PROVIDER, default=NAME_PROVIDER_DNSMASQ): voluptuous.In(NAME_PROVIDERS)
    }
)

class UbusAdvancedDeviceScanner(homeassistant.components.device_tracker.DeviceScanner):
    def __init__(self, config):
        self._logger = logging.getLogger(__name__)

        self._mac_blacklist = list(map(lambda mac: mac.upper(), config[CONF_MAC_BLACKLIST]))
        self._mac_whitelist = list(map(lambda mac: mac.upper(), config[CONF_MAC_WHITELIST]))
        self._name_blacklist = config[CONF_NAME_BLACKLIST]
        self._name_whitelist = config[CONF_NAME_WHITELIST]
        self._ssid_blacklist = config[CONF_SSID_BLACKLIST]
        self._ssid_whitelist = config[CONF_SSID_WHITELIST]

        self._ubus_client = UbusClient(self._logger, config[homeassistant.const.CONF_HOST], config[homeassistant.const.CONF_USERNAME], config[homeassistant.const.CONF_PASSWORD])
        self._ubus_client.connect()

        if config[CONF_DEVICE_PROVIDER] == DEVICE_PROVIDER_HOSTAPD:
            self._device_provider = HostapdDeviceProvider(self._logger, self._ubus_client)

        if config[CONF_NAME_PROVIDER] == NAME_PROVIDER_DNSMASQ:
            self._name_provider = DnsmasqNameProvider(self._logger, self._ubus_client)

        self._devices = []
        self._names = {}

    def scan_devices(self):
        self._logger.debug('Scanning for devices')
        self._update()

        return list(self._devices)

    def get_device_name(self, mac):
        self._logger.debug(f'Getting name for {mac} device')
        return self._names.get(mac)

    def _update(self):
        self._logger.debug('Updating data')
        devices = [device for device in self._device_provider.get() if self._filter_device(device)]
        names = [name for name in self._name_provider.get() if self._filter_name(name)]

        self._devices = [device.mac for device in devices if any(name.mac == device.mac for name in names)]
        self._names = {name.mac: name.name for name in names if any(device.mac == name.mac for device in devices)}

    def _filter_device(self, device):
        if self._mac_whitelist and device.mac not in self._mac_whitelist:
            self._logger.debug(f'Device {device} was not found on MAC address whitelist, ignoring')
            return False
        if self._mac_blacklist and device.mac in self._mac_blacklist:
            self._logger.debug(f'Device {device} was found on MAC address blacklist, ignoring')
            return False

        if self._ssid_whitelist and device.ssid not in self._ssid_whitelist:
            self._logger.debug(f'Device {device} was not found on SSID whitelist, ignoring')
            return False
        if self._ssid_blacklist and device.ssid in self._ssid_blacklist:
            self._logger.debug(f'Device {device} was found on SSID blacklist, ignoring')
            return False

        return True

    def _filter_name(self, name):
        if self._name_whitelist and not any(fnmatch.fnmatch(name.name, pattern) for pattern in self._name_whitelist):
            self._logger.debug(f'Name {name} was not found on name whitelist, ignoring')
            return False
        if self._name_blacklist and any(fnmatch.fnmatch(name.name, pattern) for pattern in self._name_blacklist):
            self._logger.debug(f'Name {name} was found on name blacklist, ignoring')
            return False

        return True

def get_scanner(hass, config):
    return UbusAdvancedDeviceScanner(config[homeassistant.components.device_tracker.DOMAIN])
