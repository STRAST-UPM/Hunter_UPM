#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# external imports
import sys
import getopt
import ast
# internal imports
from src.old_hunter.hunter import Hunter
from src.old_hunter.visualize import plot_file


def print_help_text() -> None:
    """
    Print the options available on Hunter
    """

    print("""
Usage:  
        ./hunter.sh -t IP_direction [-p probes_filepath] [-c boolean] [OPTIONS]

Commands:
Either long or short options are allowed
    --target        -t  IP_direction
                                Use HUNTER to geolocate the server where your 
                                petition goes.

Hunter Options:
    --origin        -o  "(latitude,longitude)"
                                Latitude and longitude from where Hunter will
                                start the tracking.
    --check_cf_ray  -y  boolean
                                Use it when you want to check if cf-ray used in
                                Cloudflare CDN exists (default False)
    --visualize     -v  filepath
                                Visualize the result of a measurement.
    """)


def main(argv):
    """
    Main function that execute on every run of Hunter.
    Checks input arguments and decide what code needs to be executed.
    """
    # First check for help option
    if ("-h" in argv) or ("--help" in argv):
        print_help_text()
        return

    # These sections parse the options selected and their values
    try:
        options, args = getopt.getopt(argv,
                                      "t:o:y:v",
                                      ["target", "origin",
                                       "check_cf_ray",
                                       "visualize"])
    except getopt.GetoptError as e:
        print(e)
        sys.exit(2)

    hunter = Hunter(target="")

    for option, arg in options:
        if option in ("-t", "--target"):
            hunter.set_target(arg)

        elif option in ("-o", "--origin"):
            hunter.set_origin(ast.literal_eval(arg))

        elif option in ("-y", "--check_cf_ray"):
            check_cf_ray = False
            if arg.lower() == "true":
                check_cf_ray = True
            hunter.set_check_cf_ray(check_cf_ray)

        elif option in ("-v", "--visualize"):
            try:
                visualization_filepath = args[0]
                plot_file(filepath=visualization_filepath)
                return
            except Exception as e:
                print(e)

    hunter.hunt()


if __name__ == "__main__":
    main(sys.argv[1:])

