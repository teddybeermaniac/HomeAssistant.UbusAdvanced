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
from typing import Final

CONF_MAC_BLACKLIST: Final[str] = 'mac_blacklist'
CONF_MAC_WHITELIST: Final[str] = 'mac_whitelist'
CONF_NAME_BLACKLIST: Final[str] = 'name_blacklist'
CONF_NAME_WHITELIST: Final[str] = 'name_whitelist'
CONF_SSID_BLACKLIST: Final[str] = 'ssid_blacklist'
CONF_SSID_WHITELIST: Final[str] = 'ssid_whitelist'

CONF_DEVICE_PROVIDER: Final[str] = 'device_provider'
DEVICE_PROVIDER_HOSTAPD: Final[str] = 'hostapd'
DEVICE_PROVIDERS: Final[list[str]] = [
    DEVICE_PROVIDER_HOSTAPD
]

CONF_NAME_PROVIDER: Final[str] = 'name_provider'
NAME_PROVIDER_DNSMASQ: Final[str] = 'dnsmasq'
NAME_PROVIDERS: Final[list[str]] = [
    NAME_PROVIDER_DNSMASQ
]
