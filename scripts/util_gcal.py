import logging
import apiclient
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

from dateutil.parser import parse
from collections import OrderedDict
from util_ical import *

import traceback
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

    get_named_calendar_id() - return the calendar id for the
        calendar with the given name

    does_calendar_exist() - given a calendar id, check if that
        calendar actually exists

    does_event_exist() - given a calendar id and an event id, check
        if the event exists

    get_service() - get a Google Calendar API service object


Update Methods:

    update_gcal_from_components_map() - given a map of iCalendar 
        events, use them to update the events on a Google Calendar.


Calendar Update Methods:

    add_event() - given a Google Calendar event (JSON), add the event
        to a calendar with the given calendar id. Push changes to Google
        Calendar via API.

    rm_event() - given a Google Calendar event id, remove the event
        from the calendar with the given calendar id. Push changes
        to Google Calendar via API.

    sync_events() - (MOST COMPLICATED) given a Google Calendar event (JSON) 
        and an iCalendar event (JSON), determine which fields are different
        and update those fields on Google Calendar using the API.


Create Methods:

    create_gcal() - attempt to create a new Google Calendar with the
        given label. If the calendar already exists, return its calendar
        id. If a new calendar is created, return its calendar id.

    delete_gcal() - (NOT IMPLEMENTED)

    populate_gcal_from_components_map() - iterate through every item in
        an iCalendar components map and add each ical event to the Google
        Calendar.

    gcal_components_map() - given a calendar id, add each event's JSON
        to a components map (key is event id, value is event JSON)

    gcal_components_generator() - yields JSON for events in a calendar

    ics2gcal_event() - (SUPER IMPORTANT) this converts events from 


Constants:

    FUTURE - max time to use when fetching events on a calendar
"""


FUTURE = '2018-11-01T00:00:00Z'



def get_named_calendar_id(calendar_name):
    """
    If a calendar with name calendar_name exists,
    this returns the calendar_id for that calendar.
    Otherwise, it returns None.
    """
    service = get_service()
    page_token = None
    while True:
        calendar_list = service.calendarList().list(
            pageToken=page_token
        ).execute()
        for calendar_list_entry in calendar_list['items']:
            if calendar_list_entry['summary']==calendar_name:
                return calendar_list_entry['id']
        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            return None


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


def does_event_exist(calendar_id, event_id):
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
        logging.error("Could not find OAuth credentials in credentials.json.")
        if not os.path.exists('client_secrets.json'):
            logging.error("Could not find API credentials in client_secrets.json")

            err = "Error: no API credentials for Google Calendar!\n"
            err += "Download client_secrets.json or credentials.json from the "
            err += "Google Cloud console."
            logging.error(err)
            raise Exception(err)

    SCOPES = 'https://www.googleapis.com/auth/calendar'
    store = file.Storage('credentials.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secrets.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('calendar', 'v3', http=creds.authorize(Http()))
    return service


def update_gcal_from_components_map(cal_id, components_map, force_sync=False):
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
        logging.error(err)
        raise Exception(err)

    # Get API
    service = get_service()

    logging.info("Updating Google Calendar with events from components_map...")
    logging.info("Calendar id: %s"%(cal_id))

    gcal_events = gcal_components_map(cal_id)
    ical_events = components_map

    gcal_event_ids = sorted(list(gcal_events.keys()))
    ical_event_ids = sorted(list(components_map.keys()))

    add_ids    = set(ical_event_ids) - set(gcal_event_ids)
    rm_ids     = set(gcal_event_ids) - set(ical_event_ids)
    sync_ids   = set(gcal_event_ids) & set(ical_event_ids)

    logging.info("-"*40)
    logging.info("Summary:")
    logging.info("  ADD:    %d Google Calendar events to add"%len(add_ids))
    logging.info("  REMOVE: %d Google Calendar events to remove"%len(rm_ids))
    logging.info("  SYNC:   %d Google Calendar events to sync"%len(sync_ids))

    # ----------------------------
    # Adding

    logging.info("Adding %d events..."%len(add_ids))
    add_failures = []
    for eid in add_ids:
        try:
            ical_event = ics2gcal_event(ical_events[eid])
        except:
            logging.exception("XXX Failed to convert event to JSON")
            continue
        logging.info("-"*40)
        logging.info("Adding event %s"%(eid))
        logging.info("Title: %s"%(ical_event['summary']))
        failure = add_event(ical_event,cal_id)
        if failure is None:
            logging.info("XXX Add event returned None")
            continue
        else:
            add_failures.append(failure)
    logging.info("Done adding %d events."%len(add_ids))
    logging.info("Encountered %d failures:"%len(add_failures))
    for failure in add_failures:
        eid = failure['id']
        summary = failure['summary']
        logging.info("    Event id (title): %s (%s)"%(eid, summary))

    # ----------------------------
    # Removing

    logging.info("Removing %d events..."%len(rm_ids))
    rm_failures = []
    for eid in rm_ids:
        gcal_event = gcal_events[eid]
        logging.info("-"*40)
        logging.info("Removing event %s"%(eid))
        logging.info("Title: %s"%(gcal_event['summary']))
        failure = rm_event(gcal_event,cal_id)
        if failure is None:
            continue
        else:
            rm_failures.append(failure)
    logging.info("Done removing %d events."%len(rm_ids))
    logging.info("Encountered %d failures:"%len(rm_failures))
    for failure in rm_failures:
        eid = failure['id']
        summary = failure['summary']
        logging.info("    Event id (title): %s (%s)"%(eid, summary))

    # ----------------------------
    # Sync

    logging.info("Syncing %d events..."%len(sync_ids))
    n_events_changed = 0
    for eid in sync_ids:
        gcal_event = gcal_events[eid]
        try:
            ical_event = ics2gcal_event(ical_events[eid])
        except:
            logging.exception("XXX Failed to convert ics to google calendar event")
            continue
        logging.info("-"*40)
        logging.info("Syncing event %s"%(eid))
        logging.info("Title: %s"%(ical_event['summary']))
        was_changed = sync_events(gcal_event,ical_event,cal_id,force_sync)
        if was_changed:
            n_events_changed += 1
    logging.info("Done syncing %d events, %d updated."%(len(sync_ids),n_events_changed))



def add_event(ical2gcal,cal_id):
    """
    This takes a JSON object (gcal) representing the
    google calendar event, and a calendar id.
    It adds the given event to the given calendar.
    """
    service = get_service()
    try:
        created_event = service.events().insert(calendarId=cal_id, body=ical2gcal).execute()
        logging.info("Successfully created event!")
        logging.info("Calendar id: %s"%(cal_id))
        logging.info("Event id: %s"%(created_event['id']))
        logging.info("Title: %s"%(created_event['summary']))

    except apiclient.errors.HttpError:
        if does_event_exist(cal_id, ical2gcal['id']):
            err = "ERROR: Could not create event with event id: %s\n"%(ical2gcal['id'])
            err += "This event already exists!\n"
            err += "Calendar id: %s\n"%(cal_id)
            err += "Event id: %s\n"%(ical2gcal['id'])
            err += "Title: %s\n"%(ical2gcal['summary'])
            #raise Exception(err)
            logging.error(err)
            logging.error("Continuing...\n")
            # Not a "failure", per se
            return None
        else:
            err = "ERROR: Could not create event with event id: %s\n"%(ical2gcal['id'])
            err += "There may be a problem with the calendar/event id.\n"
            err += "Calendar id: %s\n"%(cal_id)
            err += "Event id: %s\n"%(ical2gcal['id'])
            err += "Title: %s\n"%(ical2gcal['summary'])
            #raise Exception(err)
            logging.error(err)
            logging.error("Continuing...\n")
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
        logging.info("Successfully deleted event!")
        logging.info("Calendar id: %s"%(cal_id))
        logging.info("Event id: %s"%(ical2gcal['id']))

    except apiclient.errors.HttpError:
        err = "ERROR: Could not delete event with event id: %s\n"%(ical2gcal['id'])
        err += "There may be a problem with the calendar/event id.\n"
        err += "Calendar id: %s\n"%(cal_id)
        err += "Event id: %s\n"%(ical2gcal['id'])
        err += "Title: %s\n"%(gcal['summary'])
        #raise Exception(err)
        logging.error(err)
        logging.error("Continuing...\n")
        # Return this event as failed
        return ical2gcal

    return None



def sync_events(gcal, ical, cal_id, force_sync=False):
    """
    For two given events (one Google Calendar, one ical VEVENT),
    bring the Google Calendar event up to date with the 
    details of the ical event.

    Not sure what we are returning.
    """
    logging.info("Comparing ical and Google Calendar for event %s:"%(gcal['description']))

    service = get_service()

    # This entire function is run once on each individual event

    # Boolean: do we need to update the gcal event?
    # Assume no.
    update_gcal = False

    was_event_changed = False

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

    # In case we want to force two events to sync
    if not was_event_changed and force_sync:
        was_event_changed = True

    # We got here because we either:
    # 1. Found two keys that are different
    # 2. Looped over every key and found no differences

    if update_gcal:
        # Found at least two keys that are different
        # 
        # Update the gcal object, then call the
        # API with it. (Do we have the calendar id?)
        logging.info("Need to update event:")
        logging.info("    id: %s"%(gcal['id']))
        logging.info("    title: %s"%(gcal['summary']))
        logging.info("    fields changed: %s"%(", ".join(what_changed)))
        for field in what_changed:
            logging.info("        key: %s"%(field))
            logging.info("            gcal: %s"%(gcal[field]))
            logging.info("            ical: %s"%(ical[field]))
            gcal[field] = ical[field]

        try:
            # https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/calendar_v3.events.html#update
            service.events().update(calendarId=cal_id, eventId=gcal['id'], body=gcal).execute()
            logging.info("Successfully updated event!")
            logging.info("Calendar id: %s"%(cal_id))
            logging.info("Event id: %s"%(gcal['id']))
            logging.info("Title: %s"%(gcal['summary']))
            return True

        except apiclient.errors.HttpError:
            if does_event_exist(cal_id, gcal['id']):
                err = "ERROR: Could not create event with event id: %s\n"%(gcal['id'])
                err += "This event already exists!\n"
                err += "Calendar id: %s\n"%(cal_id)
                err += "Event id: %s\n"%(gcal['id'])
                err += "Title: %s\n"%(gcal['summary'])
                #raise Exception(err)
                logging.error(err)
                logging.error("Continuing...\n")
                return False
            else:
                err = "ERROR: Could not create event with event id: %s\n"%(gcal['id'])
                err += "There may be a problem with the calendar/event id.\n"
                err += "Calendar id: %s\n"%(cal_id)
                err += "Event id: %s\n"%(gcal['id'])
                err += "Title: %s\n"%(gcal['summary'])
                #raise Exception(err)
                logging.error(err)
                logging.error("Continuing...\n")
                return False

        logging.info("\n")

    else:
        logging.info("Nothing to be updated.")
        return False



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
        logging.error(err)
        raise Exception(err)

    calendar_id = get_named_calendar_id(summary)

    if calendar_id is not None:
        # Already created a calendar, so load its id
        logging.info("Found an existing \"%s\" calendar with id %s"%(summary,calendar_id))
        return calendar_id
    else:
        # This calendar does not yet exist, so let's create it

        # Get API
        service = get_service()

        try:
            calendar = {
                'summary': summary,
                'timeZone': timeZone,
            }
            created_calendar = service.calendars().insert(body=calendar).execute()
            calendar_id = created_calendar['id']
            logging.info("Finished creating a calendar \"%s\" with id %s"%(created_calendar['summary'],created_calendar['id']))
            return calendar_id

        except client.AccessTokenRefreshError:
            err = 'ERROR: Could not create test calendar\n'
            err += 'The credentials have been revoked or expired, please re-run '
            err += 'the application to re-authorize.'
            logging.error(err)
            raise Exception(err)

    return calendar_id



def destroy_gcal(calendar_id):
    """TODO: fill this one in"""
    pass




def populate_gcal_from_components_map(calendar_id, components_map):
    """
    Iterate through every event in components map
    and add it as a new event to the Google Calendar
    """
    if calendar_id is None:
        err = "ERROR: You passed a null calendar_id to populate_gcal_from_components_map()"
        logging.error(err)
        raise Exception(err)

    # Get API
    service = get_service()

    logging.info("Populating Google Calendar with events from components_map...")
    logging.info("Calendar id: %s"%(calendar_id))
    for k in components_map.keys():
        logging.info("-"*40)
        logging.info("Processing event %s"%k)
        e = components_map[k]
        try:
            gce = ics2gcal_event(e)
            add_event(gce,calendar_id)
        except:
            logging.error("XXX Failed to convert event to JSON")
            traceback.print_exc()
            continue

    gcm = gcal_components_map(calendar_id)
    logging.info("Done populating Google Calendar:")
    logging.info("Started with %d events, added %d of them"%(
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
        logging.error(err)
        raise Exception(err)

    timezone = 'UTC'
    utc = pytz.utc

    startdt = utc.localize(datetime.datetime.strptime(vevent_decode(vevent['DTSTART']), "%Y%m%dT%H%M%SZ"))
    enddt =   utc.localize(datetime.datetime.strptime(vevent_decode(vevent['DTEND']),   "%Y%m%dT%H%M%SZ"))

    event_id = get_safe_event_id(vevent_decode(vevent['UID']))
    description = htmlify_event_url(vevent)

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

