#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# external imports
import plotly.graph_objects as go
# internal imports

def flow_map_oslo():
    madrid = {
        "latitude": 40.4936,
        "longitude": -3.56676
    }
    paris = {
        "latitude": 48.7252998352,
        "longitude": 2.3594400883
    }
    milan = {
        "latitude": 45.445098877,
        "longitude": 9.2767400742
    }
    helsinki = {
        "latitude": 60.1733244,
        "longitude": 24.9410248
    }
    bucharest = {
        "latitude": 44.503200531,
        "longitude": 26.1021003723
    }
    reykjavik = {
        "latitude": 64.1299972534,
        "longitude": -21.9405994415
    }
    london = {
        "latitude": 51.5052986145,
        "longitude": 0.0552779995
    }
    zurich = {
        "latitude": 47.4646987915,
        "longitude": 8.5491695404
    }
    saint_petersburg = {
        "latitude": 59.8003005981,
        "longitude": 30.2625007629
    }
    stockholm = {
        "latitude": 59.3544006348,
        "longitude": 17.9416999817
    }
    chisinau = {
        "latitude": 47.00556,
        "longitude": 28.8575
    }
    riga = {
        "latitude": 56.9235992432,
        "longitude": 23.9710998535
    }

    flows_internal = [
        (madrid, madrid), (paris, paris), (milan, milan), (helsinki, helsinki),
        (helsinki, stockholm), (bucharest, bucharest), (bucharest, riga)
    ]
    flows_external = [
        (madrid, london), (paris, london), (milan, zurich),
        (helsinki, saint_petersburg), (bucharest, chisinau),
        (reykjavik, london)
    ]

    figure = go.Figure()

    for flow_internal in flows_internal:
        figure.add_trace(go.Scattergeo(
            lat=[flow_internal[0]["latitude"], flow_internal[1]["latitude"]],
            lon=[flow_internal[0]["longitude"], flow_internal[1]["longitude"]],
            mode="markers+lines",
            marker={"color": "blue"},
        ))

    for flow_external in flows_external:
        figure.add_trace(go.Scattergeo(
            lat=[flow_external[0]["latitude"], flow_external[1]["latitude"]],
            lon=[flow_external[0]["longitude"], flow_external[1]["longitude"]],
            mode="markers+lines",
            marker={"color": "red"},
        ))

    # Custom figure
    figure.update_geos(
       projection_type="natural earth"
    )
    figure.update_layout(
       title='Flows Map'
    )
    figure.show()

flow_map_oslo()
