#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# extrenal imports
import subprocess
from time import sleep
import datetime
# internal imports
from src.utils.constants import (
    MEASUREMENTS_CAMPAIGNS_PATH
)
from src.old_hunter.hunter import Hunter


def connect_to_vpn_server_in_country(country_code: str) -> dict:
    # Command to restore protonvpn-cli error
    # nmcli connection show --active
    connection_result = subprocess.run([
        "protonvpn-cli", "connect", "--cc",
        country_code,
        "--protocol", "tcp"], stdout=subprocess.PIPE)
    connection_status = subprocess.run([
        "protonvpn-cli", "status"], stdout=subprocess.PIPE)
    status_params_raw = (str(connection_status.stdout)
                         .split("\\n")[3:])[:-6]
    status_params = []
    for param_raw in status_params_raw:
        status_params.append((param_raw.split("\\t")[-1])[1:])
    try:
        return {
            "ip": status_params[0],
            "server_name": status_params[1],
            "country": status_params[2],
            "protocol": status_params[3],
        }
    except Exception as e:
        print(e)
        return {
            "params": status_params
        }


def disconnect_vpn():
    disconnection_result = subprocess.run([
        "protonvpn-cli", "disconnect"],
        stdout=subprocess.PIPE)


class AnycastValidationCloudfare:

    def __init__(self,
                 campaign_name: str,
                 check_cf_ray: bool = True,
                 origin: (float, float) = ()):
        self._today = datetime.datetime.utcnow().strftime('%Y%m%d_%H:%M:%S')
        self._targets_list = ["192.5.5.241", "104.16.123.96"]
        self._countries_origin = [
            "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI",
            "FR", "GR", "HR", "HU", "IE", "IS", "IT", "LT", "LU", "LV",
            "MT", "NL", "NO", "PL", "PT", "RO", "SE", "SI", "SK"
        ]

        self._origin = origin
        self._check_cf_ray = check_cf_ray

        self._campaign = "{}_{}".format(campaign_name, self._today)

    def make_vpn_campaign(self):
        # Measure from every country in list
        for country_code in self._countries_origin:
            additional_info = connect_to_vpn_server_in_country(country_code)

            while True:
                try:
                    print("Server searched {}, VPN connected {}".format(
                        country_code, additional_info["server_name"]
                    ))
                    break
                except:
                    print("Error in VPN conexion, Reconecting...")
                    additional_info = connect_to_vpn_server_in_country(
                        country_code)

            #print("Server searched {}, VPN connected {}".format(
            #    vpn_server, additional_info["server_name"]
            #))

            for target in self._targets_list:
                output_filename = "{}{}/{}_{}.json".format(
                    MEASUREMENTS_CAMPAIGNS_PATH,
                    self._campaign, target, country_code)
                hunter = Hunter(
                    target=target,
                    origin=self._origin,
                    check_cf_ray=self._check_cf_ray,
                    output_filename=output_filename,
                    additional_info=additional_info
                )
                hunter.hunt()


campaign_name = "validation_anycast_host_udp_cloudfare"
host_validator = AnycastValidationCloudfare(
    campaign_name=campaign_name,
    check_cf_ray=True
)

while True:
    hour = datetime.datetime.utcnow().hour
    execution_hours = [4, 10, 16, 22]
    if hour in execution_hours:
        host_validator.make_vpn_campaign()
        connection_result = subprocess.run(
            ["protonvpn-cli", "disconnect"],
            stdout=subprocess.PIPE
        )
    else:
        print("Waiting for the next programmed hour, now is {}".format(hour))
        print("Programmed hours of execution are {}".format(execution_hours))
        # Sleep 30 minutes
        sleep(1800)

