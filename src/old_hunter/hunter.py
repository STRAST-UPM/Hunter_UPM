#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# external imports
import pandas as pd
import requests
import geocoder
import random
import time
import subprocess
import ipinfo
from shapely import from_geojson
# internal imports
from ..utils.constants import (
    RIPE_ATLAS_MEASUREMENTS_BASE_URL,
    RIPE_ATLAS_PROBES_BASE_URL,
    KEY_FILEPATH,
    MEASUREMENTS_PATH,
    AIRPORTS_INFO_FILEPATH
)
from ..utils.common_functions import (
    json_file_to_dict,
    dict_to_json_file,
    check_discs_intersect,
    distance,
    get_distance_from_rtt,
    calculate_hunter_pings_intersection_area,
    check_ip,
    is_ipv6,
    get_nearest_airport_to_point
)


class Hunter:
    def __init__(self, target: str, origin: (float, float) = (),
                 output_filename: str = "test.json",
                 check_cf_ray: bool = True,
                 gt_info: dict = None,
                 additional_info: dict = None):
        self._target = target
        # origin format = (latitude, longitude)
        if origin != ():
            self._origin = origin
            self._traceroute_from_host = False
        else:
            try:
                (latitude, longitude) = geocoder.ip("me").latlng
            except:
                (latitude, longitude) = (0, 0)
            self._origin = (latitude, longitude)
            self._traceroute_from_host = True

        self._last_hop_validation = True
        self._target_validation = True

        self._radius = 20
        self._url = RIPE_ATLAS_MEASUREMENTS_BASE_URL + "/?key={}".format(
            self.get_ripe_key()
        )
        self._measurement_id = 0
        self._output_filename = output_filename
        self._result_filepath = ""
        self._ping_discs = []
        self._check_cf_ray = check_cf_ray
        self._gt_info = gt_info
        self._additional_info = additional_info
        self._results_measurements = {}
        self.reset_results_measurements()

    def reset_results_measurements(self):
        self._results_measurements = {
            "target": self._target,
            "origin": {
                "latitude": self._origin[0],
                "longitude": self._origin[1]
            },
            "traceroute_from_host": self._traceroute_from_host,
            "last_hop_validation": self._last_hop_validation,
            "target_validation": self._target_validation,
            "gt_info": self._gt_info,
            "result": {
                "country_result": "Indeterminate",
                "city_result": "Indeterminate",
                "advanced": {
                    "countries_list": [],
                    "cities_list": [],
                    "airports_list": [],
                    "discs_intersect": False,
                    "intersection": None,
                    "centroid": None
                }
            },
            "measurements": {
                "last_hop": {},
                "hops_directions_list": [],
                "traceroute": [],
                "ping_discs": [],
                "pings": []
            },
            "additional_info": self._additional_info
        }

    def set_target(self, target: str):
        if check_ip(target):
            self._target = target
            self.reset_results_measurements()
        else:
            print("IP direction not valid")
            return

    def set_origin(self, origin: (float, float)):
        self._origin = origin
        self._traceroute_from_host = False
        self.reset_results_measurements()

    def set_output_filename(self, filename: str):
        self._output_filename = filename

    def set_check_cf_ray(self, check_cf_ray: bool):
        self._check_cf_ray = check_cf_ray

    def set_gt_info(self, gt_info: dict):
        self._gt_info = gt_info
        self.reset_results_measurements()

    def set_additional_info(self, additional_info: dict):
        self._additional_info = additional_info
        self.reset_results_measurements()

    def hunt(self):
        if self._target is None or self._target == "":
            print("Target not valid")
            return

        if self._check_cf_ray:
            self.obtain_cf_ray()
        self.make_traceroute_measurement()
        self.build_measurement_filepath()

        if self._target_validation:
            if not self.is_target_hop_valid():
                # save ip_all_validation, failed target
                self.save_result()
                # save ip_target_validation, fail target
                self._last_hop_validation = not self._last_hop_validation
                self._results_measurements["last_hop_validation"] = \
                    self._last_hop_validation
                self.save_result()
                self._last_hop_validation = not self._last_hop_validation
                self._results_measurements["last_hop_validation"] = \
                    self._last_hop_validation
                # continue with ip_last_hop_validation and no_ip_validation
                self._target_validation = False
                self._results_measurements["target_validation"] = False
        # Geolocate last valid hop in traceroute measurement
        # save ip_all_validation, fail last_hop o
        # save _ip_last_hop_validation, fail last_hop
        last_hop = self.geolocate_last_hop()
        print("Last Hop location: ", last_hop)
        self._results_measurements["measurements"]["last_hop"] = last_hop
        if last_hop["geolocation"] == {}:
            self.save_result_with_double_target_validation()
            return

        # Pings from near last hop geo
        self.obtain_pings_near_last_hop(last_hop["geolocation"])

        # Intersection of discs from pings
        if self.check_ping_discs_intersection():
            print("All pings generated discs intersect")
            self._results_measurements["result"][
                "advanced"]["discs_intersect"] = True
            intersection_info = calculate_hunter_pings_intersection_area(
                self._results_measurements["measurements"]["ping_discs"]
            )
            self._results_measurements["result"]["advanced"]["intersection"] =\
                intersection_info["intersection"]
            self._results_measurements["result"]["advanced"]["centroid"] = \
                intersection_info["centroid"]
            # Location of airports inside intersection
            self.check_airports_inside_intersection()
        else:
            print("Some pings do not intersect. Bad scenario")

        self.save_result_with_double_target_validation()

    def make_traceroute_measurement(self):
        print("###########")
        print("Traceroute phase initiated")
        print("###########")
        print("Target to hunt: ", self._target)
        if self._traceroute_from_host:
            self.host_traceroute_measurement()
        else:
            self.ripe_traceroute_measurement()

    def host_traceroute_measurement(self):
        result_traceroute = subprocess.run([
            #"sudo",
            "traceroute",
            #"--tcp",
            #"--icmp",
            self._target], stdout=subprocess.PIPE)
        hops_list = ((str(result_traceroute.stdout)).split("\\n")[1:])[:-1]
        self._results_measurements["measurements"]["traceroute"] = hops_list

    def ripe_traceroute_measurement(self):
        # Make traceroute from origin
        probe_id = self.find_probes_in_circle(
            latitude=self._origin[0],
            longitude=self._origin[1],
            radius=self._radius,
            num_probes=1
        )
        print("Probe_ID for traceroute: ", probe_id)

        af = 6 if is_ipv6(self._target) else 4

        traceroute_data = {
            "definitions": [
                {
                    "target": self._target,
                    "description": "Hunter traceroute %s" % self._target,
                    "type": "traceroute",
                    "is_oneoff": True,
                    "af": af,
                    "protocol": "UDP",
                    "packets": 3
                }
            ],
            "probes": [
                {
                    "requested": 1,
                    "type": "probes",
                    "value": ",".join(map(str, probe_id))
                }
            ]
        }
        self.make_ripe_measurement(data=traceroute_data)
        if self._measurement_id == 0:
            print("Measure could not start")
            return
        else:
            print("Measure ID: ", self._measurement_id)
        # Obtain results
        self._results_measurements["measurements"]["traceroute"] = \
            self.get_measurement_results()

    def make_ripe_measurement(self, data: dict):
        # Start the measurement and get measurement id
        response = {}
        try:
            response = requests.post(self._url, json=data).json()
            self._measurement_id = response["measurements"][0]
        except Exception as e:
            print(e.__str__())
            print(response)

    def get_probes_scheduled(self) -> int:
        probes_scheduled_url = RIPE_ATLAS_MEASUREMENTS_BASE_URL + \
                               "{}/?fields=probes_scheduled".format(
                                   self._measurement_id)
        retrieved = False
        while not retrieved:
            time.sleep(1)
            try:
                response = requests.get(probes_scheduled_url).json()
                return int(response["probes_scheduled"])
            except:
                print("Measure not scheduled yet")

    def build_measurement_filepath(self):
        if self._output_filename == "hunter_measurement.json":
            filename = "{}_{}_{}_{}.json".format(
                self._target,
                self._origin[0], self._origin[1],
                self._measurement_id)
            self._result_filepath = MEASUREMENTS_PATH + filename
        else:
            self._result_filepath = MEASUREMENTS_PATH + self._output_filename

    def add_validation_suffix(self):
        if self._target_validation and self._last_hop_validation:
            suffix = "ip_all_validation"
        elif self._target_validation and not self._last_hop_validation:
            suffix = "ip_target_validation"
        elif not self._target_validation and self._last_hop_validation:
            suffix = "ip_last_hop_validation"
        else:
            suffix = "no_ip_validation"

        self.build_measurement_filepath()
        filename = self._result_filepath[:-5]
        filename = filename + "_" + suffix
        self._result_filepath = filename + ".json"

    def get_measurement_results(self) -> list:
        results_measurement_url = \
            RIPE_ATLAS_MEASUREMENTS_BASE_URL + "{}/results".format(
                self._measurement_id
            )
        delay = 5
        enough_results = False
        attempts = 0
        response = []

        while not enough_results:
            print("Wait {} seconds for results. Number of attempts {}".
                  format(delay, attempts))
            time.sleep(delay)
            delay = 15
            attempts += 1
            probes_scheduled = self.get_probes_scheduled()
            print("Total probes scheduled for measurement: ", probes_scheduled)
            response = requests.get(results_measurement_url).json()
            print("Obtained response from {} probes".format(len(response)))
            if len(response) == probes_scheduled:
                print("Results retrieved")
                enough_results = True
            elif attempts >= 10:
                enough_results = True
            else:
                enough_results = False
        return response

    def geolocate_last_hop(self) -> dict:
        directions_list = self.build_hops_directions_list()
        print("Traceroute directions: ")
        [print(direction) for direction in directions_list]
        if self._last_hop_validation:
            last_hop = self.select_last_hop_valid(directions_list)
            if last_hop["geolocation"] == {}:
                # save ip_all_validation + ip_last_hop_validation,
                # fail last_hop
                self.save_result()
                self._target_validation = not self._target_validation
                self._results_measurements["target_validation"] = \
                    self._target_validation
                self.save_result()
                self._target_validation = not self._target_validation
                self._results_measurements["target_validation"] = \
                    self._target_validation
                # continue with ip_target_validation and no_ip_validation save
                self._last_hop_validation = False
                self._results_measurements["last_hop_validation"] = False

        last_hop = {"ip": "", "geolocation": {}}
        for last_hop_ip in directions_list[-2]:
            if last_hop_ip != "*":
                try:
                    location = self.geolocate_with_ipinfo(ip=last_hop_ip)
                    last_hop = {
                        "ip": last_hop_ip,
                        "geolocation": location
                    }
                except:
                    continue
                break
            else:
                continue

        print("Last Hop IP direction valid: ", last_hop["ip"])
        return last_hop

    def select_last_hop_valid(self, directions_list: list) -> dict:
        validated = False
        last_hop_index = -2
        last_hop_direction = ""
        last_hop_geo = {}

        last_hop = {
            "ip": last_hop_direction,
            "geolocation": last_hop_geo
        }

        if (len(directions_list) + last_hop_index) < 0:
            print("Last_hop index out of range")
            return last_hop

        last_hop_directions = directions_list[last_hop_index]
        if not self.hop_from_directions_are_equal(last_hop_directions):
            print("Last_hop have more than one IP")
            return last_hop

        last_hop_direction = last_hop_directions[0]
        if "*" == last_hop_direction:
            print("Last_hop does not respond")
            last_hop_direction = ""
        elif last_hop_direction == self._target:
            print("Last_hop direction is same than target")
            last_hop_direction = ""

        try:
            # TODO geolocate last_hop_direction better
            last_hop_geo = self.geolocate_with_ipinfo(
                ip=last_hop_direction)
        except Exception as e:
            print("Exception in last_hop geolocation")
            print(e)

        last_hop = {
            "ip": last_hop_direction,
            "geolocation": last_hop_geo
        }
        return last_hop

    def is_target_hop_valid(self) -> bool:
        target_hop = self._results_measurements["measurements"]["hops_directions_list"]
        if len(target_hop) == 1 and target_hop[0] == self._target:
            return True
        else:
            return False

    def build_hops_directions_list(self) -> list:
        directions_list = []
        if self._traceroute_from_host:
            for result in self._results_measurements["measurements"]["traceroute"]:
                hop_directions = []
                for split in result.split(" "):
                    if split == "":
                        continue
                    elif split == "*":
                        hop_directions.append(split)
                    elif split[0] == "(" and split[-1] == ")":
                        hop_directions.append(split[1:-1])
                    else:
                        continue
                hop_directions = list(dict.fromkeys(hop_directions))
                directions_list.append(hop_directions)
        else:
            traceroute_results = \
                self._results_measurements["traceroute"][0]["result"]
            for hop in traceroute_results:
                hop_directions = []
                for hop_result in hop["result"]:
                    if "x" in hop_result.keys():
                        hop_directions.append("*")
                    else:
                        hop_directions.append(hop_result["from"])
                hop_directions = list(dict.fromkeys(hop_directions))
                directions_list.append(hop_directions)

        self._results_measurements["measurements"]["hops_directions_list"] = \
            directions_list
        return directions_list

    def obtain_pings_near_last_hop(self, last_hop_geo: dict):
        print("###########")
        print("Pings phase initiated")
        print("###########")
        # Make pings from probes around last_hop_geo
        probes_id_list = self.find_probes_in_circle(
            latitude=last_hop_geo["latitude"],
            longitude=last_hop_geo["longitude"],
            radius=self._radius,
            num_probes=7
        )

        af = 6 if is_ipv6(self._target) else 4

        pings_data = {
            "definitions": [
                {
                    "target": self._target,
                    "description": "Hunter pings %s" % self._target,
                    "type": "ping",
                    "is_oneoff": True,
                    "af": af,
                    "packets": 3
                }
            ],
            "probes": [
                {
                    "requested": len(probes_id_list),
                    "type": "probes",
                    "value": ",".join(map(str, probes_id_list))
                }
            ]
        }
        self.make_ripe_measurement(data=pings_data)
        if self._measurement_id == 0:
            print("Measure could not start")
            return
        else:
            print("Measure ID: ", self._measurement_id)
        # Obtain results
        self._results_measurements["measurements"]["pings"] = \
            self.get_measurement_results()

    def check_ping_discs_intersection(self) -> bool:
        # Build discs
        for ping_result in self._results_measurements["measurements"]["pings"]:
            min_rtt = ping_result["min"]
            ping_radius = get_distance_from_rtt(min_rtt)
            probe_location = self.get_probe_coordinates(ping_result["prb_id"])
            self._ping_discs.append({
                "probe_id": ping_result["prb_id"],
                "latitude": probe_location["latitude"],
                "longitude": probe_location["longitude"],
                "rtt_min": ping_result["min"],
                "radius": ping_radius
            })

        self._results_measurements["measurements"]["ping_discs"] = \
            self._ping_discs

        if all(ping["radius"] == -1 for ping in self._ping_discs):
            return False

        # Check all disc intersection
        for disc1 in self._ping_discs:
            for disc2 in self._ping_discs:
                if disc1 == disc2:
                    continue
                elif disc1["radius"] == -1 or disc2["radius"] == -1:
                    continue
                elif check_discs_intersect(disc1, disc2):
                    continue
                else:
                    return False
        return True

    def check_airports_inside_intersection(self):
        airports_df = pd.read_csv(AIRPORTS_INFO_FILEPATH, sep="\t")
        airports_df.drop(["pop",
                          "heuristic",
                          "1", "2", "3"], axis=1, inplace=True)

        def check_inside_intersection(airport_code) -> bool:
            airport_to_check = airports_df[
                (airports_df["#IATA"] == airport_code)
            ]
            lat_long_string = airport_to_check["lat long"].values[0]
            (airport_lat, airport_lon) = lat_long_string.split(" ")
            a = {"latitude": float(airport_lat),
                 "longitude": float(airport_lon)}
            for disc in self._ping_discs:
                b = {"latitude": disc["latitude"],
                     "longitude": disc["longitude"]}
                if distance(a=a, b=b) < disc["radius"]:
                    continue
                else:
                    return False
            return True

        airports_df["inside_intersection"] = airports_df["#IATA"].apply(
            lambda airport_code: check_inside_intersection(airport_code)
        )

        airports_inside_df = airports_df[(
                airports_df["inside_intersection"] == True
        )].copy()

        cities_results = list(airports_inside_df["city"].unique())
        countries_results = list(airports_inside_df["country_code"].unique())
        airports_inside_df.drop(["inside_intersection"], axis=1, inplace=True)
        airports_inside_df.rename(columns={"#IATA": "IATA_code"}, inplace=True)
        airports_located = airports_inside_df.to_dict("records")
        for airport_located in airports_located:
            (lat, lon) = airport_located["lat long"].split(" ")
            airport_located["latitude"] = float(lat)
            airport_located["longitude"] = float(lon)
            airport_located.pop("lat long", None)

        if len(airports_located) == 0:
            centroid = from_geojson(
                self._results_measurements["result"]["advanced"]["centroid"])
            airports_located = [get_nearest_airport_to_point(point=centroid)]

            cities_results = [airports_located[0]["city"]]
            countries_results = [airports_located[0]["country_code"]]

        if len(cities_results) == 1:
            self._results_measurements["result"]["city_result"] = \
                cities_results[0]
        else:
            self._results_measurements["result"]["city_result"] = \
                "Indeterminate"

        if len(countries_results) == 1:
            self._results_measurements["result"]["country_result"] = \
                countries_results[0]
        else:
            self._results_measurements["result"]["country_result"] = \
                "Indeterminate"

        self._results_measurements["result"]["advanced"]["cities_list"] = \
            cities_results
        self._results_measurements["result"]["advanced"]["countries_list"] = \
            countries_results
        self._results_measurements["result"]["advanced"]["airports_list"] = \
            airports_located

        print("Cities locations detected: ")
        [print(city) for city in cities_results]
        print("Countries detected: ")
        [print(country) for country in countries_results]

    def save_result(self):
        self.add_validation_suffix()
        dict_to_json_file(self._results_measurements, self._result_filepath)

    def save_result_with_double_target_validation(self):
        if self._target_validation and self._last_hop_validation:
            # save ip_all_validation, target and last_hop good
            self.save_result()
            # save ip_last_hop_validation, last_hop good
            self._target_validation = False
            self._results_measurements["target_validation"] = False
            self.save_result()
            # save ip_target_validation, target good
            self._target_validation = True
            self._results_measurements["target_validation"] = True
            self._last_hop_validation = False
            self._results_measurements["last_hop_validation"] = False
            self.save_result()
            # save no_ip_validation
            self._target_validation = False
            self._results_measurements["target_validation"] = False
            self.save_result()
        elif not self._target_validation and self._last_hop_validation:
            # ip_all_validation already saved with fail target
            # save ip_last_hop_validation, last_hop good
            self.save_result()
            # ip_target_validation already saved with fail target
            # save no_ip_validation
            self._last_hop_validation = False
            self._results_measurements["last_hop_validation"] = False
            self.save_result()
        elif self._target_validation and not self._last_hop_validation:
            # ip_all_validation already saved with fail last_hop
            # ip_last_hop_validation already saved with fail last_hop

            # save ip_target_validation, target good
            self.save_result()
            # save no_ip_validation
            self._target_validation = False
            self._results_measurements["target_validation"] = False
            self.save_result()
        else:
            # ip_all_validation already saved with fail target
            # ip_last_hop_validation already saved with fail last_hop
            # ip_target_validation with fail target ???

            # save no_ip_validation
            self.save_result()

# Not class exclusive functions

    def find_probes_in_circle(self,
                              latitude: float, longitude: float,
                              radius: float, num_probes: int) -> list:
        radius_filter = "radius={},{}:{}".format(latitude, longitude, radius)
        connected_filter = "status_name=Connected"
        fields = "fields=id,geometry,address_v4"
        url = "{}?{}&{}&{}".format(RIPE_ATLAS_PROBES_BASE_URL,
                                   radius_filter,
                                   connected_filter,
                                   fields)
        probes_inside = requests.get(url=url).json()
        not_target_ip_probes = list(filter(
            lambda probe: probe["address_v4"] != self._target,
            probes_inside["results"]
        ))
        if len(not_target_ip_probes) == 0:
            print("No probes in a {} km circle.".format(radius))
            return self.find_probes_in_circle(
                latitude=latitude,
                longitude=longitude,
                radius=radius + 10,
                num_probes=num_probes
            )
        elif len(not_target_ip_probes) < num_probes:
            print("Less than {} probes suitable in area".format(num_probes))
            return self.find_probes_in_circle(
                latitude=latitude,
                longitude=longitude,
                radius=radius + 10,
                num_probes=num_probes
            )
        else:
            probes_selected = random.sample(not_target_ip_probes, num_probes)
            ids_selected = [probe["id"] for probe in probes_selected]
            return ids_selected

    def get_ripe_key(self) -> str:
        return json_file_to_dict(KEY_FILEPATH)["ripe_token"]

    def hop_from_directions_are_equal(self, hop_directions_list: list) -> bool:
        if len(hop_directions_list) != 1:
            return False
        else:
            return True

    def geolocate_with_geocoder(self, ip: str) -> dict:
        (latitude, longitude) = geocoder.ip(ip).latlng
        return {
            "latitude": latitude,
            "longitude": longitude
        }

    def geolocate_with_ipinfo(self, ip: str) -> dict:
        access_token = json_file_to_dict(KEY_FILEPATH)["ipinfo_token"]
        handler = ipinfo.getHandler(access_token)
        details = handler.getDetails(ip)
        return {
            "latitude": details.latitude,
            "longitude": details.longitude
        }

    def get_probe_coordinates(self, probe_id: int) -> dict:
        url = RIPE_ATLAS_PROBES_BASE_URL + "/%s" % probe_id
        probe_response = requests.get(url).json()

        latitude = probe_response["geometry"]["coordinates"][1]
        longitude = probe_response["geometry"]["coordinates"][0]
        return {
            "latitude": latitude,
            "longitude": longitude
        }

    # def make_box_centered_on_origin(self) -> Polygon:
    #     return box(xmin=self._origin[0] - self._separation,
    #                ymin=self._origin[1] - self._separation,
    #                xmax=self._origin[0] + self._separation,
    #                ymax=self._origin[1] + self._separation)

    def obtain_cf_ray(self):
        try:
            headers = requests.get("http://{}".format(self._target)).headers
            cf_ray_iata_code = headers["cf-ray"].split("-")[1]

            airports_df = pd.read_csv(AIRPORTS_INFO_FILEPATH, sep="\t")
            airports_df.drop(["pop",
                              "heuristic",
                              "1", "2", "3"], axis=1, inplace=True)
            mask = airports_df["#IATA"].values == cf_ray_iata_code
            airport_cf_ray = airports_df[mask].to_dict("records")[0]

            self._results_measurements["gt_info"] = airport_cf_ray

        except Exception as e:
            print("NO CF-RAY IN HEADERS")


