#!/usr/bin/env python
import sys 
from pprint import pprint
from oauth2client import client
from googleapiclient import sample_tools

# sample_tools is where they tucked away all the magic and swept it all under the rug
# https://github.com/google/google-api-python-client/blob/master/googleapiclient/sample_tools.py
#
# name of the api: find a list of apis and links to reference here:
# https://developers.google.com/api-client-library/python/apis/
#
# pydoc:
# https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/

def main(argv):
    # Authenticate and construct service.
    service, flags = sample_tools.init(
        argv, 'calendar', 'v3', 
        __doc__, __file__,
        scope='https://www.googleapis.com/auth/calendar')

    try:
        calendar = {
            'summary': 'This is a test calendar',
            'timeZone': 'America/Los_Angeles'
        }
        created_calendar = service.calendars().insert(body=calendar).execute()
        print(created_calendar['id'])

    except client.AccessTokenRefreshError:
        print('The credentials have been revoked or expired, please re-run'
              'the application to re-authorize.')

    try:
        # see https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/calendar_v3.events.html#insert
        # for a list of valid fields.
        # these should map to ical VEVENT fields.
        #
        # SUMMARY
        # DTSTART
        # DTEND
        # UID -> leads to unique Groups.io URL
        # SEQUENCE
        # DESCRIPTION
        # LOCATION
        # ORGANIZER
        event = {}
        created_events = created_calendar.events().insert(body=event).execute()

if __name__ == '__main__':
    main(sys.argv)


