#!/usr/bin/env python
import sys, os

from util_gcal import *
from util_ical import *


"""
gcal update calendar

utilize two versions of an .ics calendar file:
- create an initial calendar
- popullate initial calendar with events from version A
- make modifications with version B
- verify that updates were propagated
- delete temporary calendar

structure this like a test.

eventually will have command line options
to control what steps are being run.
"""

# name of the api: find a list of apis and links to reference here:
# https://developers.google.com/api-client-library/python/apis/
#
# pydoc:
# https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/


FUTURE = '2018-11-01T00:00:00Z'



def populate_calendar(ical_file):

    calendar_id = create_gcal("Another Test GCal Integration")

    # get all vevents
    components_map = ics_components_map(get_ical_contents(ical_file))
    print("Preparing to add %d events to the calendar."%len(components_map.keys()))

    # add each event to google calendar
    populate_gcal_from_components_map(calendar_id, components_map)


def update_calendar(ical_file):

    calendar_id = create_gcal("Another Test GCal Integration")

    # get all vevents
    components_map = ics_components_map(get_ical_contents(ical_file))

    # add each event to google calendar
    update_gcal_from_components_map(calendar_id, components_map)


if __name__ == '__main__':
    ## Step 1: populate with calendar A
    #populate_calendar('../samples/integrated_calendar_A.ics')
    
    ## Step 2: smoke test with calendar A
    #update_calendar('../samples/integrated_calendar_A.ics')

    # Step 3: update with calendar B
    update_calendar('../samples/integrated_calendar_B.ics')

