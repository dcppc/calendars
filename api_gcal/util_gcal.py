import apiclient
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

from dateutil.parser import parse
from collections import OrderedDict
from util_ical import *

from pprint import pprint
import sys, os, re
import datetime
import pytz

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
FUTURE = '2018-11-01T00:00:00Z'


def does_calendar_exist(calendar_id):
    """
    Boolean: does this calendar_id exist?
    """
    service = get_service()
    page_token = None
    while True:
        calendar_list = service.calendarList().list(
            pageToken=page_token
        ).execute()
        for calendar_list_entry in calendar_list['items']:
            if calendar_list_entry['id']==calendar_id:
                return True
        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            return False


def event_exists(calendar_id, event_id):
    """
    Boolean: does the event with id event_id
    exist on calendar with id calendar_id?
    """
    service = get_service()
    page_token = None
    while True:
        events_list = service.events().list(
                calendarId=calendar_id, 
                pageToken = page_token,
                timeMax=FUTURE
        ).execute()

        for events_list_entry in events_list['items']:
            if events_list_entry['id']==event_id:
                return True

        page_token = events_list.get('nextPageToken')
        if not page_token:
            return False


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
        f.write(cal_id)
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

    print("Loaded calendar id from file %s"%(CAL_ID_FILE))
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
        calendar_id = load_cal_id()
        return calendar_id

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

    return calendar_id



def destroy_gcal(calendar_id):
    # Get an instance of cal calendar_id
    # and delete the calendar
    # (don't forget to delete the cal id file too)
    pass



def update_gcal_from_components_map(cal_id, components_map):
    """
    Iterate through every event in components map
    and check if this event exists on the Google Calendar.

    If the event does not exist, create it.

    If the event does exist, compare the component event
    and the Google Calendar event to see if Google Calendar
    needs to be updated.
    """
    if cal_id is None:
        err = "ERROR: You passed a null cal_id to populate_gcal_from_components_map()"
        raise Exception(err)

    # Get API
    service = get_service()

    print("Updating Google Calendar with events from components_map...")
    print("Calendar id: %s"%(cal_id))

    gcal_events = gcal_components_map(cal_id)
    ical_events = components_map

    gcal_event_ids = sorted(list(gcal_events.keys()))
    ical_event_ids = sorted(list(components_map.keys()))

    add_ids    = set(ical_event_ids) - set(gcal_event_ids)
    rm_ids     = set(gcal_event_ids) - set(ical_event_ids)
    sync_ids   = set(gcal_event_ids) & set(ical_event_ids)

    print("-"*40)
    print("Summary:")
    print("  ADD:    %d Google Calendar events to add"%len(add_ids))
    print("  REMOVE: %d Google Calendar events to remove"%len(rm_ids))
    print("  SYNC:   %d Google Calendar events to sync"%len(sync_ids))

    # ----------------------------
    # Adding

    print("Adding %d events..."%len(add_ids))
    add_failures = []
    for eid in add_ids:
        ical_event = ics2gcal_event(ical_events[eid])
        print("-"*40)
        print("Adding event %s"%(eid))
        print("Title: %s"%(ical_event['summary']))
        failure = add_event(ical_event,cal_id)
        if failure is None:
            pass
        else:
            add_failures.append(failure)
    print("Done adding %d events."%len(add_ids))
    print("Encountered %d failures:"%len(add_failures))
    for failure in add_failures:
        eid = failure['id']
        summary = failure['summary']
        print("    Event id (title): %s (%s)"%(eid, summary))

    # ----------------------------
    # Removing

    print("Removing %d events..."%len(rm_ids))
    rm_failures = []
    for eid in rm_ids:
        gcal_event = gcal_events[eid]
        print("-"*40)
        print("Removing event %s"%(eid))
        print("Title: %s"%(gcal_event['summary']))
        failure = rm_event(gcal_event,cal_id)
        if failure is None:
            pass
        else:
            rm_failures.append(failure)
    print("Done removing %d events."%len(rm_ids))
    print("Encountered %d failures:"%len(rm_failures))
    for failure in rm_failures:
        eid = failure['id']
        summary = failure['summary']
        print("    Event id (title): %s (%s)"%(eid, summary))

    # ----------------------------
    # Sync

    print("Syncing %d events..."%len(sync_ids))
    for eid in sync_ids:
        gcal_event = gcal_events[eid]
        ical_event = ics2gcal_event(ical_events[eid])
        print("-"*40)
        print("Syncing event %s"%(eid))
        print("Title: %s"%(ical_event['summary']))
        sync_events(gcal_event,ical_event,cal_id)
    print("Done syncing %d events."%len(sync_ids))



def add_event(ical2gcal,cal_id):
    """
    This takes a JSON object (gcal) representing the
    google calendar event, and a calendar id.
    It adds the given event to the given calendar.
    """
    service = get_service()
    try:
        created_event = service.events().insert(calendarId=cal_id, body=ical2gcal).execute()
        print("Successfully created event!")
        print("Calendar id: %s"%(cal_id))
        print("Event id: %s"%(created_event['id']))
        print("Title: %s"%(created_event['summary']))

    except apiclient.errors.HttpError:
        if event_exists(cal_id, ical2gcal['id']):
            err = "ERROR: Could not create event with event id: %s\n"%(ical2gcal['id'])
            err += "This event already exists!\n"
            err += "Calendar id: %s\n"%(cal_id)
            err += "Event id: %s\n"%(ical2gcal['id'])
            err += "Title: %s\n"%(ical2gcal['summary'])
            #raise Exception(err)
            print(err)
            print("Continuing...\n")
            # Not a "failure", per se
            return None
        else:
            err = "ERROR: Could not create event with event id: %s\n"%(ical2gcal['id'])
            err += "There may be a problem with the calendar/event id.\n"
            err += "Calendar id: %s\n"%(cal_id)
            err += "Event id: %s\n"%(ical2gcal['id'])
            err += "Title: %s\n"%(ical2gcal['summary'])
            #raise Exception(err)
            print(err)
            print("Continuing...\n")
            # Return this event as failed
            return ical2gcal

    return None


def rm_event(ical2gcal,cal_id):
    """
    This takes a JSON object (gcal) representing the
    google calendar event, and a calendar id.
    It removes the given event from the given calendar.
    """
    service = get_service()
    try:
        service.events().delete(calendarId=cal_id, eventId=ical2gcal['id'], sendNotifications=False)
        print("Successfully deleted event!")
        print("Calendar id: %s"%(cal_id))
        print("Event id: %s"%(ical2gcal['id']))

    except apiclient.errors.HttpError:
        err = "ERROR: Could not delete event with event id: %s\n"%(ical2gcal['id'])
        err += "There may be a problem with the calendar/event id.\n"
        err += "Calendar id: %s\n"%(cal_id)
        err += "Event id: %s\n"%(ical2gcal['id'])
        err += "Title: %s\n"%(gcal['summary'])
        #raise Exception(err)
        print(err)
        print("Continuing...\n")
        # Return this event as failed
        return ical2gcal

    return None



def sync_events(gcal,ical,cal_id):
    """
    For two given events (one Google Calendar, one ical VEVENT),
    bring the Google Calendar event up to date with the 
    details of the ical event.

    Not sure what we are returning.
    """
    print("Comparing ical and Google Calendar for event %s:"%(gcal['description']))

    service = get_service()

    # This entire function is run once on each individual event

    # Boolean: do we need to update the gcal event?
    # Assume no.
    update_gcal = False

    what_changed = []

    # Iterate over each key in the given event
    for ik in ical.keys():

        # ical event keys are a subset of google cal event keys,
        # so only check keys that exist in ical
        if ik in gcal.keys():

            # If the values of these matching keys
            # do not match, we need to update the
            # Google Calendar event
            if ical[ik]!=gcal[ik]:

                # UNLESS.........
                # It is a start or end time, in which case,
                # we need to make sure we are comparing the 
                # timestamps correctly.
                if ik=='start' or ik=='end':

                    # Example output:
                    # 
                    #(Pdb) ical[ik]
                    #{'timeZone': 'UTC', 'dateTime': '2018-10-04T17:00:00+00:00'}
                    #(Pdb) gcal[ik]
                    #{'dateTime': '2018-10-04T13:00:00-04:00', 'timeZone': 'UTC'}

                    # Get the datetime strings
                    if 'dateTime' not in ical[ik].keys():
                        # Yikes...
                        continue

                    if 'dateTime' not in gcal[ik].keys():
                        # We shouldn't be here.
                        continue

                    # Now for the tricky part.
                    # Parse the datetime stamps
                    idt = parse(ical[ik]['dateTime'])
                    gdt = parse(gcal[ik]['dateTime'])

                    # ASSUMPTION:
                    # We assume that Groups.io .ics calendars
                    # are ALWAYS given in the UTC timeZone.
                    # If we update our Google Calendar event
                    # and use a timestamp in the UTC timezone,
                    # Google Calendar will automatically add
                    # the time zone information for this calendar
                    # to the given event.
                    # 
                    # (Calendars are EASTERN TIME by default.)
                    # 
                    # Okay, on with the show.
                    # Convert gcal event datetime to UTC
                    # so we can compare to ical datetime.
                    gdt = gdt.astimezone(pytz.timezone('UTC'))

                    if gdt != idt:
                        # The start/end time has changed
                        what_changed.append(ik)
                        update_gcal = True
                        # Keep going so we have a complete
                        # list of keys that changed with
                        # this particular event.

                elif ik=='sequence':
                    # Sequence may be an integer
                    # or a string... :-/
                    if str(gcal[ik])!=str(ical[ik]):
                        what_changed.append(ik)
                        update_gcal = True

                elif ik=='organizer':
                    # The organizer automatically gets reset to 
                    # the owner of the calendar, so there's no
                    # need to worry about it.
                    pass

                else:

                    # Neither a start nor an end,
                    # and the keys are unequal.
                    # No further questions.
                    what_changed.append(ik)
                    update_gcal = True


    # We got here because we either:
    # 1. Found two keys that are different
    # 2. Looped over every key and found no differences

    if update_gcal:
        # Found at least two keys that are different
        # 
        # Update the gcal object, then call the
        # API with it. (Do we have the calendar id?)
        print("Need to update event:")
        print("    id: %s"%(gcal['id']))
        print("    title: %s"%(gcal['summary']))
        print("    fields changed: %s"%(", ".join(what_changed)))
        for field in what_changed:
            print("        key: %s"%(field))
            print("            gcal: %s"%(gcal[field]))
            print("            ical: %s"%(ical[field]))
            gcal[field] = ical[field]

        try:
            # https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/calendar_v3.events.html#update
            service.events().update(calendarId=cal_id, eventId=gcal['id'], body=gcal).execute()
            print("Successfully updated event!")
            print("Calendar id: %s"%(cal_id))
            print("Event id: %s"%(gcal['id']))
            print("Title: %s"%(gcal['summary']))

        except apiclient.errors.HttpError:
            if event_exists(cal_id, gcal['id']):
                err = "ERROR: Could not create event with event id: %s\n"%(gcal['id'])
                err += "This event already exists!\n"
                err += "Calendar id: %s\n"%(cal_id)
                err += "Event id: %s\n"%(gcal['id'])
                err += "Title: %s\n"%(gcal['summary'])
                #raise Exception(err)
                print(err)
                print("Continuing...\n")
            else:
                err = "ERROR: Could not create event with event id: %s\n"%(gcal['id'])
                err += "There may be a problem with the calendar/event id.\n"
                err += "Calendar id: %s\n"%(cal_id)
                err += "Event id: %s\n"%(gcal['id'])
                err += "Title: %s\n"%(gcal['summary'])
                #raise Exception(err)
                print(err)
                print("Continuing...\n")

        print("\n")

    else:
        print("Nothing to be updated.")




def populate_gcal_from_components_map(calendar_id, components_map):
    """
    Iterate through every event in components map
    and add it as a new event to the Google Calendar
    """
    if calendar_id is None:
        err = "ERROR: You passed a null calendar_id to populate_gcal_from_components_map()"
        raise Exception(err)

    # Get API
    service = get_service()

    print("Populating Google Calendar with events from components_map...")
    print("Calendar id: %s"%(calendar_id))
    for k in components_map.keys():
        print("-"*40)
        print("Processing event %s"%k)
        e = components_map[k]
        gce = ics2gcal_event(e)
        add_event(gce,calendar_id)

    gcm = gcal_components_map(calendar_id)
    print("Done populating Google Calendar:")
    print("Started with %d events, added %d of them"%(
        len(components_map.keys()), 
        len(gcm.keys())
    ))



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



def ics2gcal_event(vevent):

    if 'UID' not in vevent.keys():
        err = "ERROR: Passed a vevent to ics2gcal_event() that has no UID!\n"
        err += vevent.to_ical().decode('utf-8')
        raise Exception(err)

    timezone = 'UTC'
    utc = pytz.utc

    startdt = utc.localize(datetime.datetime.strptime(vevent_decode(vevent['DTSTART']), "%Y%m%dT%H%M%SZ"))
    enddt =   utc.localize(datetime.datetime.strptime(vevent_decode(vevent['DTEND']),   "%Y%m%dT%H%M%SZ"))

    event_id = get_safe_event_id(vevent_decode(vevent['UID']))
    description = get_event_url(vevent)

    keys = ['SUMMARY','SEQUENCE','LOCATION','ORGANIZER']
    for key in keys:
        if key not in vevent:
            vevent[key] = b''

    gcal_event = {
            "summary" : vevent_decode(vevent['SUMMARY']),
            "start" : {
                "timeZone" : timezone,
                "dateTime" : startdt.isoformat("T"),
            },
            "end" : {
                "timeZone" : timezone,
                "dateTime" : enddt.isoformat("T"),
            },
            "id" :          event_id,
            "sequence" :    vevent_decode(vevent['SEQUENCE']),
            "location" :    vevent_decode(vevent['LOCATION']),
            "description" : description,
            "organizer" : {
                "displayName" : vevent_decode(vevent['ORGANIZER']),
            }
    }

    return gcal_event

