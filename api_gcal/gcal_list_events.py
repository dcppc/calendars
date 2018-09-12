#!/usr/bin/env python
import sys 
from pprint import pprint
from oauth2client import client
from googleapiclient import sample_tools

# sample_tools is where they tucked away all the magic and swept it all under the rug
# https://github.com/google/google-api-python-client/blob/master/googleapiclient/sample_tools.py

# name of the api: find a list of apis and links to reference here:
# https://developers.google.com/api-client-library/python/apis/

def main(argv):
    # Authenticate and construct service.
    service, flags = sample_tools.init(
        argv, 'calendar', 'v3', 
        __doc__, __file__,
        scope='https://www.googleapis.com/auth/calendar.readonly')

    try:
        max_time = '2018-11-01T00:00:00Z'
        page_token = None
        while True:

            calendar_list = service.calendarList().list(pageToken=page_token).execute()
            for calendar_list_entry in calendar_list['items']:

                cal_id = calendar_list_entry['id']

                events_list = service.events().list(calendarId=cal_id, timeMax=max_time).execute()
                for events_list_entry in events_list['items']:

                    print(events_list_entry)

            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break

    except client.AccessTokenRefreshError:
        print('The credentials have been revoked or expired, please re-run'
              'the application to re-authorize.')

if __name__ == '__main__':
    main(sys.argv)


