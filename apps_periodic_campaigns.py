#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

# external imports
import pandas as pd
import subprocess
import datetime
from shapely import from_geojson
from time import sleep

# internal imports
from src.utils.constants import (
    STATISTICS_PATH,
)
from src.utils.common_functions import (
    json_file_to_dict,
    countries_in_EEE_set,
    get_list_files_in_path,
    get_nearest_airport_to_point
)
from src.old_hunter.hunter import Hunter


def hunt_popets_anycast(campaign: str, anycast_directions_filepath: str):
    popets_ip_dict = json_file_to_dict(anycast_directions_filepath)
    anycast_ip_list = [ip for ip in popets_ip_dict.keys()
                       if popets_ip_dict[ip]]
    anycast_ip_list.sort()

    countries_origin = [
            "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI",
            "FR", "GR", "HR", "HU", "IE", "IS", "IT", "LT", "LU", "LV",
            "MT", "NL", "NO", "PL", "PT", "RO", "SE", "SI", "SK"
        ]

    for country in countries_origin:
        while True:
            additional_info = connect_to_vpn_server(country)
            try:
                server_country = additional_info["server_name"].split("#")[0]
                if country == server_country:
                    print("Server searched {}, VPN connected {}".format(
                        country, additional_info["server_name"]
                    ))
                    break
                else:
                    disconnect_vpn()
            except Exception as e:
                print("VPN Connection Failed with exception: {}".format(e))
                print("Reconnecting")
                disconnect_vpn()

        for target in anycast_ip_list:
            output_filename = \
                "./apps_analysis/measurements/{}/{}_{}.json".format(
                    campaign, target, country)
            hunter = Hunter(
                target=target,
                check_cf_ray=False,
                output_filename=output_filename,
                additional_info=additional_info,
            )
            hunter.hunt()


def connect_to_vpn_server(vpn_server: str) -> dict:
    # Command to restore protonvpn-cli error
    # nmcli connection show --active
    connection_result = subprocess.run([
        "protonvpn-cli", "connect", "--cc",
        vpn_server,
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

while True:
    hour = datetime.datetime.utcnow().hour
    execution_hours = [9]
    if hour in execution_hours:
        # Apps comunications measurements
        start_time = datetime.datetime.utcnow().strftime('%Y%m%d_%H:%M:%S')
        campaign_name = "PoPETs_anycast_ipinfo_" + start_time
        # Take measurements
        hunt_popets_anycast(
            campaign=campaign_name,
            anycast_directions_filepath="./apps_analysis/PoPETs_anycast_pii_ips_ip_info.json"
        )
        finish_time = datetime.datetime.utcnow().strftime('%Y%m%d_%H:%M:%S')

        print("Start execution at {}".format(start_time))
        print("Finish execution at {}".format(finish_time))
    else:
        print("Waiting for the next programmed hour, now is {}".format(hour))
        print("Programmed hours of execution are {}".format(execution_hours))
        sleep(1800)


