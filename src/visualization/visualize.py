#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# external imports
import plotly.graph_objects as go
import shapely
from shapely import Point, Polygon, MultiPolygon

# internal imports
from ..utils.common_functions import (
    json_file_to_dict,
    convert_km_radius_to_degrees,
)


def plot_file(filepath: str) -> None:
    try:
        data_keys = json_file_to_dict(filepath).keys()
    except Exception as e:
        print("Exception provocated because bad file")
        print(e)
        return

    if "last_hop" in data_keys:
        plot_hunter_result(filepath)
    else:
        print("File not recognized")


def plot_hunter_result(filepath: str) -> None:
    hunter_result = json_file_to_dict(filepath)
    fig = go.Figure()
    # Add origin
    fig.add_trace(go.Scattergeo(
        lat=[hunter_result["origin"]["latitude"]],
        lon=[hunter_result["origin"]["longitude"]],
        mode="markers",
        marker={"color": "green"},
        name="origin"
    ))
    # Add last hop
    fig.add_trace(go.Scattergeo(
        lat=[hunter_result["last_hop"]["geolocation"]["latitude"]],
        lon=[hunter_result["last_hop"]["geolocation"]["longitude"]],
        mode="markers",
        marker={"color": "blue"},
        name="last_hop"
    ))
    # Add pings valid
    discs_to_intersect = []
    probes_latitudes = []
    probes_longitudes = []
    for ping_disc in hunter_result["ping_discs"]:
        probes_latitudes.append(ping_disc["latitude"])
        probes_longitudes.append(ping_disc["longitude"])
        disc = Point(
            ping_disc["longitude"],
            ping_disc["latitude"]
        ).buffer(convert_km_radius_to_degrees(ping_disc["radius"]))
        discs_to_intersect.append(disc)

    fig.add_trace(go.Scattergeo(
        lat=probes_latitudes,
        lon=probes_longitudes,
        mode="markers",
        marker={"color": "magenta"},
        name="ping_probes"
    ))

    ###
    for disc in discs_to_intersect:
        disc_ext_coords_x, disc_ext_coords_y = disc.exterior.coords.xy

        fig.add_trace(go.Scattergeo(
            lat=disc_ext_coords_y.tolist(),
            lon=disc_ext_coords_x.tolist(),
            mode="markers+lines",
            marker={"color": "red"},
            name="ping_discs"
        ))
    ##

    intersection = shapely.intersection_all(discs_to_intersect)
    intersection_ext_coords_x, \
        intersection_ext_coords_y = intersection.exterior.coords.xy
    fig.add_trace(go.Scattergeo(
        lat=intersection_ext_coords_y.tolist(),
        lon=intersection_ext_coords_x.tolist(),
        mode="markers+lines",
        marker={"color": "goldenrod"},
        name="pings_intersection"
    ))
    # Add airports located
    airports_latitudes = [
        airport["latitude"]
        for airport in hunter_result["hunt_results"]["airports_located"]
    ]
    airports_longitudes = [
        airport["longitude"]
        for airport in hunter_result["hunt_results"]["airports_located"]
    ]
    fig.add_trace(go.Scattergeo(
        lat=airports_latitudes,
        lon=airports_longitudes,
        mode="markers",
        marker={"color": "red"},
        name="airports_result"
    ))

    # Add GT location
    try:
        gt_info = hunter_result["gt_info"]
        (gt_latitude, gt_longitude) = gt_info["lat long"].split(" ")
        fig.add_trace(go.Scattergeo(
            lat=[gt_latitude],
            lon=[gt_longitude],
            mode="markers",
            marker={"color": "black"},
            name="gt"
        ))
    except Exception as e:
        print("No GT info")


    # Custom figure
    fig.update_geos(
        projection_type="natural earth"
    )
    fig.update_layout(
        title='Hunter Result'
    )
    fig.show()


def plot_polygon(polygon: Polygon):
    longitudes = []
    latitudes = []

    polygon_ext_coords_x, polygon_ext_coords_y = polygon.exterior.coords.xy
    longitudes = longitudes + polygon_ext_coords_x.tolist()
    latitudes = latitudes + polygon_ext_coords_y.tolist()

    fig = go.Figure(data=go.Scattergeo(
        lon=longitudes,
        lat=latitudes,
        mode='markers'
    ))
    fig.update_geos(
        projection_type="natural earth"
    )
    fig.update_layout(
        title='Test Mesh'
    )
    fig.show()


def plot_multipolygon(multipolygon: MultiPolygon):
    longitudes = []
    latitudes = []
    for polygon in list(multipolygon.geoms):
        polygon_ext_coords_x, polygon_ext_coords_y = polygon.exterior.coords.xy
        longitudes = longitudes + polygon_ext_coords_x.tolist()
        latitudes = latitudes + polygon_ext_coords_y.tolist()

    fig = go.Figure(data=go.Scattergeo(
        lon=longitudes,
        lat=latitudes,
        mode='markers'
    ))
    fig.update_geos(
        projection_type="natural earth"
    )
    fig.update_layout(
        title='Test Mesh'
    )
    fig.show()
