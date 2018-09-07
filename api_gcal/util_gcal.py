import sys, os
import datetime
import pytz
from pprint import pprint
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

"""
Google Calendar API Utilities


Description:

This file contains utility methods for interfacing
with the Google Calendar API.


Utility Methods:

get_service() - provides an API object (service) to allow
interaction with the Google Calendar API.

save_cal_id() - save the calendar id to the calendar id file.

load_cal_id() - load the calendar id from the calendar id file.


Calendar Methods:

create_calendar() - create a calendar, take a summary and
time zone as arguments, save to calendar id file.

get_event_ids() - get a set of event ids from a specified
calendar id.





Constants:


CAL_ID_FILE - the name of the file containing the
id of the temporary calendar created. Used to modify
events on the same calendar later.
"""


CAL_ID_FILE = 'calendar_name.txt'


def get_service():
    """
    Get a service object, which provides an API interface.
    See pydocs here: 
    https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/
    """
    SCOPES = 'https://www.googleapis.com/auth/calendar'
    store = file.Storage('credentials.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secrets.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('calendar', 'v3', http=creds.authorize(Http()))
    return service


def save_cal_id(cal_id):
    """
    Save the calendar id in the calendar id file
    """
    with open(CAL_ID_FILE,'w') as f:
        f.write(calendar_id)
    print("Stored calendar id in file %s"%(CAL_ID_FILE))


def load_cal_id():
    """
    Load the calendar id in the calendar id file
    """
    if not os.path.exists(CAL_ID_FILE):
        err = "ERROR: Could not load calendar id from file %s: "%(CAL_ID_FILE)
        err += "No file"
        raise Exception(err)

    with open(CAL_ID_FILE,'r') as f:
        calendar_id = f.read()

    if calendar_id == '':
        err = "ERROR: Could not load calendar id from file %s: "%(CAL_ID_FILE)
        err += "Empty file"
        raise Exception(err)

    return calendar_id


def create_calendar(summary,timeZone="America/New_York"):
    """
    Create a calendar with a brief description in summary
    and specifying the time zone.

    Acceptable time zones:
    - America/New_York
    - America/Chicago
    - America/Denver
    - America/Los_Angeles
    """
    if summary=="":
        err = "ERROR: Calendar summary was empty"
        raise Exception(err)

    # Get API
    service = get_service()

    calendar_id = None
    try:
        calendar = {
            'summary': summary,
            'timeZone': timeZone,
        }
        print("Creating calendar...")
        created_calendar = service.calendars().insert(body=calendar).execute()
        calendar_id = created_calendar['id']
        print("Done. Created calendar with id: %s"%(calendar_id))

    except client.AccessTokenRefreshError:
        err = 'ERROR: Could not create test calendar\n'
        err += 'The credentials have been revoked or expired, please re-run '
        err += 'the application to re-authorize.'
        raise Exception(err)



def get_event_ids(calendar_id):
    """
    Return a set containing all unique event IDs
    for events on this particular calendar.
    """
    # Get API
    service = get_service()

    event_ids = set()

    page_token = None
    while True:

        calendar_list = service.calendarList().list(pageToken=page_token).execute()
        for calendar_list_entry in calendar_list['items']:

            cal_id = calendar_list_entry['id']

            max_time = '2018-11-01T00:00:00Z'
            events_list = service.events().list(calendarId=cal_id, timeMax=max_time).execute()
            for events_list_entry in events_list['items']:

                event_ids.add(events_list_entry['id'])

        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break

    print("Extracted events from calendar %s:"%(calendar_id))
    print(event_ids)
    return event_ids




