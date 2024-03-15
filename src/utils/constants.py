#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###############################################################################

# Data for operation path
__DATA_PATH = "src/resources/"

# Alone files
AIRPORTS_INFO_FILEPATH = __DATA_PATH + "airports.csv"
KEY_FILEPATH = __DATA_PATH + "keys.json"
COUNTRY_BORDERS_GEOJSON_FILEPATH = \
    __DATA_PATH + \
    "UIA_Latitude_Longitude_Graticules_and_World_Countries_Boundaries.geojson"
VERLOC_APROX_PATH = __DATA_PATH + "verloc_aprox.json"

# Countries sets
COUNTRIES_SETS_PATH = __DATA_PATH + "countries_sets/"
ALL_COUNTRIES_FILE_PATH = COUNTRIES_SETS_PATH + "all_countries.json"
EU_COUNTRIES_FILE_PATH = COUNTRIES_SETS_PATH + "EU_countries.json"
EEE_COUNTRIES_FILE_PATH = COUNTRIES_SETS_PATH + "EEE_countries.json"
NORTH_CENTRAL_COUNTRIES_FILE_PATH = COUNTRIES_SETS_PATH + \
                                    "North-Central_countries.json"
ADEQUATE_INTERNATIONAL_TRANSFER_COUNTRIES_FILE_PATH = \
    COUNTRIES_SETS_PATH + "adequate_international_transfer_countries.json"

# Ground Truth
__GROUND_TRUTH_PATH = __DATA_PATH + "ground-truth/"
ROOT_SERVERS_PATH = __GROUND_TRUTH_PATH + "root_servers/"
CLOUDFARE_PATH = __GROUND_TRUTH_PATH + "cloudfare/"

###############################################################################

# Results path
__RESULTS_PATH = "results/"

# Measurements
MEASUREMENTS_PATH = __RESULTS_PATH + "measurements/"
MEASUREMENTS_CAMPAIGNS_PATH = MEASUREMENTS_PATH + "campaigns/"

# Statistics
STATISTICS_PATH = __RESULTS_PATH + "statistics/"

###############################################################################

# URLs
ROOT_SERVERS_URL = "https://root-servers.org/root/"
RIPE_ATLAS_API_BASE_URL = "https://atlas.ripe.net/api/v2/"
RIPE_ATLAS_MEASUREMENTS_BASE_URL = RIPE_ATLAS_API_BASE_URL + "measurements/"
RIPE_ATLAS_PROBES_BASE_URL = RIPE_ATLAS_API_BASE_URL + "probes/"

# Others
ROOT_SERVERS_NAMES = [
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M"
]
ROOT_SERVERS = {
    "198.41.0.4": "root_servers_A.json",
    "199.9.14.201": "root_servers_B.json",
    "192.33.4.12": "root_servers_C.json",
    "199.7.91.13": "root_servers_D.json",
    "192.203.230.10": "root_servers_E.json",
    "192.5.5.241": "root_servers_F.json",
    "192.112.36.4": "root_servers_G.json",
    "198.97.190.53": "root_servers_H.json",
    "192.36.148.17": "root_servers_I.json",
    "192.58.128.30": "root_servers_J.json",
    "193.0.14.129": "root_servers_K.json",
    "199.7.83.42": "root_servers_L.json",
    "202.12.27.33": "root_servers_M.json"
}
CLOUDFARE_IPS = ["104.16.123.96"]
EARTH_RADIUS_KM = 6371
NEAR_CITY_TP_KM = 100
# Units = [km/s]
SPEED_OF_LIGHT = 299792.458
VERLOC_GAP = 5
