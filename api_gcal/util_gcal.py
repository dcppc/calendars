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
    if not os.path.exists('credentials.json'):
        print("Could not find OAuth credentials in credentials.json.")
        if not os.path.exists('client_secrets.json'):
            print("Could not find API credentials in client_secrets.json")

            err = "Error: no API credentials for Google Calendar!\n"
            err += "Download client_secrets.json or credentials.json from the "
            err += "Google Cloud console."
            raise Exception(err)

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


def create_gcal(summary,timeZone="America/New_York"):
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

    if os.path.exists(CAL_ID_FILE):
        # Already created a calendar, so load its id
        print("Found a calendar ID file at %s"%(CAL_ID_FILE))
        return

    else:
        # Create a new calendar

        # Get API
        service = get_service()

        calendar_id = None
        try:
            calendar = {
                'summary': summary,
                'timeZone': timeZone,
            }
            print("Creating calendar file %s"%(CAL_ID_FILE))
            created_calendar = service.calendars().insert(body=calendar).execute()
            calendar_id = created_calendar['id']
            save_cal_id(calendar_id)
            print("Done. Created calendar with id: %s"%(calendar_id))

        except client.AccessTokenRefreshError:
            err = 'ERROR: Could not create test calendar\n'
            err += 'The credentials have been revoked or expired, please re-run '
            err += 'the application to re-authorize.'
            raise Exception(err)

        print("Finished creating a calendar id file at %s"%(CAL_ID_FILE))



def destroy_gcal(calendar_id):
    # Get an instance of cal calendar_id
    # and delete the calendar
    # (don't forget to delete the cal id file too)
    pass



def populate_gcal_from_components_map(calendar_id, components_map):
    # This is where we get an instance of cal calendar_id
    # and iterate through each event in components_map
    # and add each event to the calendar
    pass





def gcal_components_map(calendar_id, components_map={}):
    for e in gcal_components_generator(calendar_id):
        components_map[e['id']] = e
    return components_map



def gcal_components_generator(calendar_id):
    """
    Given a calendar id as a string,
    get the calendar and iterate through
    each event (component), yielding
    the JSON for the object as we go
    """
    # Get API
    service = get_service()

    while True:
        events_list = service.events().list(calendarId=calendar_id, timeMax=FUTURE).execute()
        for events_list_entry in events_list['items']:
            yield events_list_entry
        page_token = events_list.get('nextPageToken')
        if not page_token:
            break


