#!/usr/bin/env python
import sys, os
import datetime
import pytz
from pprint import pprint
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

# sample_tools is where they tucked away all the magic and swept it all under the rug
# https://github.com/google/google-api-python-client/blob/master/googleapiclient/sample_tools.py
#
# name of the api: find a list of apis and links to reference here:
# https://developers.google.com/api-client-library/python/apis/
#
# pydoc:
# https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/

def get_service():
    SCOPES = 'https://www.googleapis.com/auth/calendar'
    store = file.Storage('credentials.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secrets.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('calendar', 'v3', http=creds.authorize(Http()))
    return service

def create_calendar():

    # Get API
    service = get_service()

    calendar_id = None
    try:
        calendar = {
            'summary': 'Test Calendar',
            'timeZone': 'America/Los_Angeles'
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

    with open('calendar_name.txt','w') as f:
        f.write(calendar_id)


def populate_calendar():

    calendar_file = 'calendar_name.txt'

    if not os.path.exists(calendar_file):
        err = "ERROR: Could not load calendar id from file %s: "%(calendar_file)
        err += "No file"
        raise Exception(err)

    with open('calendar_name.txt','r') as f:
        calendar_id = f.read()

    if calendar_id == '':
        err = "ERROR: Could not load calendar id from file %s: "%(calendar_file)
        err += "Empty file"
        raise Exception(err)

    calendar_id = calendar_id.strip()
    print("Adding events to calendar %s"%(calendar_id))

    # Get API
    service = get_service()

    try:
        # see https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/calendar_v3.events.html#insert
        # for a list of valid fields.
        #
        # ooh: import:
        # import_(calendarId=*, body=*, supportsAttachments=None, conferenceDataVersion=None)
        #   Imports an event. This operation is used to add a private copy of an existing event to a calendar.
        #
        #
        # these should map to ical VEVENT fields.
        #
        # SUMMARY
        #       "summary": "A String", # Title of the event.
        #
        # DTSTART
        #     "start": { # The (inclusive) start time of the event. For a recurring event, this is the start time of the first instance.
        #            "date": "A String", # The date, in the format "yyyy-mm-dd", if this is an all-day event.
        #            "timeZone": "A String", # The time zone in which the time is specified. (Formatted as an IANA Time Zone Database name, e.g. "Europe/Zurich".) For recurring events this field is required and specifies the time zone in which the recurrence is expanded. For single events this field is optional and indicates a custom time zone for the event start/end.
        #            "dateTime": "A String", # The time, as a combined date-time value (formatted according to RFC3339). A time zone offset is required unless a time zone is explicitly specified in timeZone.
        #       },
        #
        # DTEND
        #
        #     "end": { # The (exclusive) end time of the event. For a recurring event, this is the end time of the first instance.
        #            "date": "A String", # The date, in the format "yyyy-mm-dd", if this is an all-day event.
        #            "timeZone": "A String", # The time zone in which the time is specified. (Formatted as an IANA Time Zone Database name, e.g. "Europe/Zurich".) For recurring events this field is required and specifies the time zone in which the recurrence is expanded. For single events this field is optional and indicates a custom time zone for the event start/end.
        #            "dateTime": "A String", # The time, as a combined date-time value (formatted according to RFC3339). A time zone offset is required unless a time zone is explicitly specified in timeZone.
        #       },
        #
        # UID -> leads to unique Groups.io URL
        #      (???)  "htmlLink": "A String", # An absolute link to this event in the Google Calendar Web UI. Read-only.
        #
        # SEQUENCE
        #      "sequence": 42, # Sequence number as per iCalendar.
        #
        # DTCREATED
        #      "created": "A String", # Creation time of the event (as a RFC3339 timestamp). Read-only.
        #
        # DESCRIPTION
        #       "description": "A String", # Description of the event. Optional.
        #
        # LOCATION
        #      "location": "A String", # Geographic location of the event as free-form text. Optional.
        #
        # ORGANIZER
        #       "organizer": { # The organizer of the event. If the organizer is also an attendee, this is indicated with a separate entry in attendees with the organizer field set to True. To change the organizer, use the move operation. Read-only, except when importing an event.
        #               "self": false, # Whether the organizer corresponds to the calendar on which this copy of the event appears. Read-only. The default is False.
        #               "displayName": "A String", # The organizer's name, if available.
        #               "email": "A String", # The organizer's email address, if available. It must be a valid email address as per RFC5322.
        #               "id": "A String", # The organizer's Profile ID, if available. It corresponds to the id field in the People collection of the Google+ API
        #       },
        # 
        #

        #mytz = 'US/Eastern'
        #eastern = pytz.timezone(mytz)

        mytz = 'UTC'
        utc = pytz.utc

        print("Creating event...")
        startdt =   utc.localize(datetime.datetime.strptime('2018-09-05 17:30:00','%Y-%m-%d %H:%M:%S'))
        enddt =     utc.localize(datetime.datetime.strptime('2018-09-05 18:30:00','%Y-%m-%d %H:%M:%S'))
        createddt = utc.localize(datetime.datetime.strptime('2018-08-11 10:17:23','%Y-%m-%d %H:%M:%S'))
        event = {
                'summary' : 'Something Something Meeting',
                'description' : 'Well I say old chap, check out the link like a good sport, here you go: https://dcppc.groups.io/g/kc6tech/viewevent?repeatid=6402&eventid=311498&calstart=2018-09-04',
                'start' : {
                    'dateTime' : startdt.isoformat("T"),
                    'timeZone' : mytz,
                },
                'end' : {
                    'dateTime' : enddt.isoformat("T"),
                    'timeZone' : mytz,
                },
                'htmlLink' : 'https://dcppc.groups.io/g/kc6tech/viewevent?repeatid=6402&eventid=311498&calstart=2018-09-04',
                'sequence' : 1,
                'location' : 'The Moon',
                'organizer' : {
                    'email' : 'sample@email.com',
                    'displayName' : 'Some Person'
                }
        }
        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
        print("Done. Created event with id: %s"%(created_event['id']))

    except client.AccessTokenRefreshError:
        err = 'ERROR: Could not create test event\n'
        err += 'The credentials have been revoked or expired, please re-run '
        err += 'the application to re-authorize.'

if __name__ == '__main__':
    #create_calendar()
    populate_calendar()
