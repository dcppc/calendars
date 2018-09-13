import argparse
import os
import sys


basename = os.path.split(os.path.abspath(__file__))[0]


"""
DCPPC Calendar Creation Script

This is a command line utility for creating and updating
the DCPPC integrated calendar on Google Calendar.

The script integrates multiple .ics feeds from Groups.io
subgroups into a single Google Calendar, and keeps them
synchronized.

The user should use either the create or update flag.
They should also provide a file containing .ical URLs,
one URL per line.

Example of creating a new calendar:

    python dcppc_calendar.py --create \
            --name="DCPPC Calendar" \
            --ical-list=ical_list.txt

Example of updating the existing calendar:

    python dcppc_calendar.py --update \
            --name="DCPPC Calendar" \
            --ical-list=ical_list.txt
"""

class ValidationException(Exception):
    pass


def main():
    args = parse_args()
    if args.create:
        create_calendar(args)
    else:
        update_calendar(args)


def die(parser):
    """Print parser help and die"""
    parser.print_help(sys.stderr)
    exit(1)


def parse_args():
    """
    Parse the user arguments
    """
    descr = "This script creates/updates an integrated calendar of DCPPC events. "
    descr += "Pass either the --create or --update flag. "
    descr += "The --ical-list flag is required and should point to a file "
    descr += "with one .ics URL per line."
    descr += "The --name flag is optional."

    parser = argparse.ArgumentParser(description=descr)
    parser.add_argument(
            '-c', '--create', 
            action='store_true',
            help='(REQUIRED) Create a new Google Calendar with integrated calendar events'
    )
    parser.add_argument(
            '-u', '--update', 
            action='store_true',
            help='(REQUIRED) Update (sync) an existing Google Calendar with integrated calendar events'
    )
    parser.add_argument(
            '-i', '--ical-list', 
            help='(REQUIRED) Name of a file containing a list of .ics URLs, one per line'
    )
    parser.add_argument(
            '-n', '--name', 
            default = "DCPPC Calendar",
            help='(OPTIONAL) Name of the calendar ("DCPPC Calendar" by default)'
    )
    args = parser.parse_args()

    validate(parser)

    if args.create:
        print("Creating calendar \"%s\""%args.name)
    elif args.update:
        print("Updating calendar \"%s\""%args.name)
    else:
        die(parser)

    return parser


def validate(parser):
    """
    Validate the input arguments provided by the user
    """
    args = parser.parse_args()
    if (args.create and args.update):
        err = "ERROR: both create and update arguments were specified."
        err += "You must specify one or the other.\n"
        print(err)
        die(parser)

    if ((not args.create) and (not args.create)):
        err = "ERROR: Neither create nor update arguments were specified."
        err += "You must specify one or the other.\n"
        print(err)
        die(parser)

    if not os.path.isfile(args.ical_list):
        err = "ERROR: Could not find ical file at %s "%(args.ical_list)
        raise ValidationException(err)


def create_calendar(args):

    # create the calendar and return the calendar id
    calendar_id = create_gcal(args.name)

    # get all icals
    icals = []
    with open(args.ical_list,'r') as f:
        icals = f.readlines()

    # get all vevents
    components_map = {}
    for ical_url in icals:
        components_map = ics_components_map(get_calendar_contents(ical_url), component_map)

    print("Preparing to add %d events to the calendar."%len(components_map.keys()))

    # add each event to google calendar
    populate_gcal_from_components_map(calendar_id, components_map)


def update_calendar(args):

    # return the calendar id
    calendar_id = create_gcal(args.name)

    # get all icals
    icals = []
    with open(args.ical_list,'r') as f:
        icals = f.readlines()

    # get all vevents
    components_map = {}
    for ical_url in icals:
        components_map = ics_components_map(get_calendar_contents(ical_url), component_map)

    print("Preparing to update %d events on the calendar."%len(components_map.keys()))

    # add each event to google calendar
    update_gcal_from_components_map(calendar_id, components_map)


if __name__=="__main__":
    main()

