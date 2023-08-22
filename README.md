# Home Assistant Ubus Advanced integration
Home Assistant device tracker which uses OpenWRT's ubus.

## Installation
* Install HACS - [HACS Setup].
* Add `https://github.com/teddybeermaniac/HomeAssistant.UbusAdvanced` repository to HACS - [HACS Custom Repositories].
* Install the integration using HACS.

## Setup
### On router
* Create a `/usr/share/rpcd/acl.d/homeassistant.json` file. Adapt `/tmp/dhcp.leases` according to `leasefile` options in your `/etc/config/dhcp` configuration file (you can use wildcards here):
    ```json
    {
        "homeassistant": {
            "description": "HomeAssistant Ubus Advanced integration",
            "read": {
                "file": {
                    "/tmp/dhcp.leases": [
                        "read"
                    ]
                },
                "ubus": {
                    "file": [
                        "read"
                    ],
                    "hostapd.*": [
                        "get_clients",
                        "get_status"
                    ],
                    "uci": [
                        "get"
                    ]
                },
                "uci": [
                    "dhcp"
                ]
            }
        }
    }
    ```
    See [OpenWRT Wiki ubus/ACLs] for more details.
* Add `/usr/share/rpcd/acl.d/homeassistant.json` to `/etc/sysupgrade.conf` file to prevent it from being deleted during upgrade.
* Add a section to `/etc/config/rpcd`. The password can be generated using `uhttpd -m password`:
    ```ini
    config login
            option username 'homeassistant'
            option password '$1$$I2o9Z7NcvQAKp7wyCTlia0'
            list read 'homeassistant'
            list write 'homeassistant'
    ```
    See [OpenWRT Wiki ubus/Authentication] for more details.
* Restart rpcd `/etc/init.d/rpcd restart`.

### In Home Assistant
* Add device tracker to `configuration.yaml`. Use your router's IP, or hostname and username, and plaintext version of password that you added to `/etc/config/rpcd`:
    ```yaml
    device_tracker:
      - platform: ubus_advanced
        host: http://192.168.0.1
        username: homeassistant
        password: password
        # Example options
        ssid_blacklist:
          - Guest WiFi
    ```
    See [Home Assistant device_tracker] for more details.

## Configuration options
|Name|Required|Default|Description|
|-|-|-|-|
|host|✅||IP/Hostname of your router|
|username|✅||`username` from `/etc/config/rpcd` section|
|password|✅||Plaintext `password` from `/etc/config/rpcd` section|
|mac_blacklist||`[]`|Device MAC address blacklist|
|mac_whitelist||`[]`|Device MAC address whitelist|
|name_blacklist||`[]`|Device DHCP name blacklist (supports wildcards)|
|name_whitelist||`[]`|Device DHCP name whitelist (supports wildcards)|
|ssid_blacklist||`[]`|SSID blacklist|
|ssid_whitelist||`[]`|SSID whitelist|
|device_provider||`hostapd`|How to acquire device list. One of: `hostapd`|
|name_provider||`dnsmasq`|How to acquire device name mapping. One of: `dnsmasq`|

Other common options can be found in [Home Assistant device_tracker].

[HACS Custom Repositories]: https://hacs.xyz/docs/faq/custom_repositories
[HACS Setup]: https://hacs.xyz/docs/setup/prerequisites
[Home Assistant device_tracker]: https://www.home-assistant.io/integrations/device_tracker
[OpenWRT Wiki ubus/ACLs]: https://openwrt.org/docs/techref/ubus#acls
[OpenWRT Wiki ubus/Authentication]: https://openwrt.org/docs/techref/ubus#authentication
