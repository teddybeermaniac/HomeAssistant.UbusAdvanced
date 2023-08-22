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
from fnmatch import fnmatch
from homeassistant.components.device_tracker import (
    DOMAIN,
    PLATFORM_SCHEMA as DEVICE_TRACKER_PLATFROM_SCHEMA,
    DeviceScanner
)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation
from homeassistant.helpers.typing import ConfigType
from logging import getLogger
from voluptuous import All, In, Optional, Required
from voluptuous.validators import Length
from .const import *
from .model import Device, Name
from .name_provider import DnsmasqNameProvider
from .device_provider import HostapdDeviceProvider
from .ubus_client import UbusClient

PLATFORM_SCHEMA = DEVICE_TRACKER_PLATFROM_SCHEMA.extend(
    {
        Required(CONF_HOST): config_validation.url_no_path,
        Required(CONF_USERNAME): config_validation.string,
        Required(CONF_PASSWORD): config_validation.string,
        Optional(CONF_MAC_BLACKLIST, default=[]): All(config_validation.ensure_list, [config_validation.string, config_validation.matches_regex('^[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}$')]),
        Optional(CONF_MAC_WHITELIST, default=[]): All(config_validation.ensure_list, [config_validation.string, config_validation.matches_regex('^[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}$')]),
        Optional(CONF_NAME_BLACKLIST, default=[]): All(config_validation.ensure_list, [config_validation.string]),
        Optional(CONF_NAME_WHITELIST, default=[]): All(config_validation.ensure_list, [config_validation.string]),
        Optional(CONF_SSID_BLACKLIST, default=[]): All(config_validation.ensure_list, [config_validation.string, Length(1, 32)]),
        Optional(CONF_SSID_WHITELIST, default=[]): All(config_validation.ensure_list, [config_validation.string, Length(1, 32)]),
        Optional(CONF_DEVICE_PROVIDER, default=DEVICE_PROVIDER_HOSTAPD): In(DEVICE_PROVIDERS),
        Optional(CONF_NAME_PROVIDER, default=NAME_PROVIDER_DNSMASQ): In(NAME_PROVIDERS)
    }
)

class UbusAdvancedDeviceScanner(DeviceScanner): #type: ignore
    def __init__(self, config: ConfigType):
        self._logger = getLogger(__name__)

        self._mac_blacklist = list(map(lambda mac: mac.upper(), config[CONF_MAC_BLACKLIST]))
        self._mac_whitelist = list(map(lambda mac: mac.upper(), config[CONF_MAC_WHITELIST]))
        self._name_blacklist = config[CONF_NAME_BLACKLIST]
        self._name_whitelist = config[CONF_NAME_WHITELIST]
        self._ssid_blacklist = config[CONF_SSID_BLACKLIST]
        self._ssid_whitelist = config[CONF_SSID_WHITELIST]

        self._ubus_client = UbusClient(self._logger, config[CONF_HOST], config[CONF_USERNAME], config[CONF_PASSWORD])
        self._ubus_client.connect()

        if config[CONF_DEVICE_PROVIDER] == DEVICE_PROVIDER_HOSTAPD:
            self._device_provider = HostapdDeviceProvider(self._logger, self._ubus_client)

        if config[CONF_NAME_PROVIDER] == NAME_PROVIDER_DNSMASQ:
            self._name_provider = DnsmasqNameProvider(self._logger, self._ubus_client)

        self._devices: list[str] = []
        self._names: dict[str, str] = {}

    def scan_devices(self) -> list[str]:
        self._logger.debug('Scanning for devices')
        self._update()

        return list(self._devices)

    def get_device_name(self, mac: str) -> str | None:
        self._logger.debug(f'Getting name for {mac} device')
        return self._names.get(mac)

    def _update(self) -> None:
        self._logger.debug('Updating data')
        devices = [device for device in self._device_provider.get() if self._filter_device(device)]
        names = [name for name in self._name_provider.get() if self._filter_name(name)]

        self._devices = [device.mac for device in devices if any(name.mac == device.mac for name in names)]
        self._names = {name.mac: name.name for name in names if any(device.mac == name.mac for device in devices)}

    def _filter_device(self, device: Device) -> bool:
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

    def _filter_name(self, name: Name) -> bool:
        if self._name_whitelist and not any(fnmatch(name.name, pattern) for pattern in self._name_whitelist):
            self._logger.debug(f'Name {name} was not found on name whitelist, ignoring')
            return False
        if self._name_blacklist and any(fnmatch(name.name, pattern) for pattern in self._name_blacklist):
            self._logger.debug(f'Name {name} was found on name blacklist, ignoring')
            return False

        return True

def get_scanner(hass: HomeAssistant, config: ConfigType) -> DeviceScanner:
    return UbusAdvancedDeviceScanner(config[DOMAIN])
