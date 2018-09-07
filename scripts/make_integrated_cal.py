from icalendar import Calendar, Event
import re, os

from util_ical import get_calendar_contents


"""
make integrated calendar


This script iterates over each subgroup .ics calendar file
and extracts all of the events. It then adds those events
to a master .ics calendar file.
"""


# ahhhhh
# https://icalendar.org/validator.html

SCRIPT_DIR = os.path.split(os.path.abspath(__file__))[0]

ICSLINKS_DIR = os.path.join(SCRIPT_DIR,'..')
ICSLINKS_FILE = 'ics_links.txt'

HTDOCS_DIR = '/www/calendars.nihdatacommons.us/htdocs'

### # Testing: output to ../samples/
### ICS_DIR = os.path.join(SCRIPT_DIR,'..','samples')

# Real deal: output to htdocs dir
ICS_DIR = os.path.join(HTDOCS_DIR)

# Leave this alone
ICS_FILE = 'integrated_calendar.ics'



def main():
    """
    Make an integrated .ics calendar file
    """

    # Get list of ics URLs
    icsfile = os.path.join(ICSLINKS_DIR,ICSLINKS_FILE)
    with open(icsfile,'r') as f:
        urls = f.readlines()
    
    # Scrape contents of ics file and add to list
    calendar_contents = []
    for ics_url in urls:

        # Given an .ics url, extract the .ics file contents
        # as a string and add it to the calendar_contents list
        result = get_calendar_contents(ics_url)
        calendar_contents.append(result)

    components_map = {}
    for ics in calendar_contents:
        components_map = ics_components_map(ics, components_map)

    newcal = new_calendar_from_components_map(
            "Data Commons Calendar",
            components_map
    )

    icsfile = os.path.join(ICS_DIR,ICS_FILE)
    export_ical_file(newcal,icsfile)

if __name__=="__main__":
    main()
