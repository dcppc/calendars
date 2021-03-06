import logging
from icalendar import Calendar, Event
import re, os
import requests


"""
iCalendar Utilties


Description:

    This file contains utility methods for dealing with
    .ics icalendar files.

Calendar Methods:

    export_ical_file() - export a Calendar() object to an .ics file

    new_calendar_from_components_map() - use a map of component IDs to
        calendar VEVENTS to create a new calendar

    ics_components_map() - given the contents of an .ics file as a string,
        convert to a map of UIDs to VEVENT component objects

    ics_components_generator() - given the contents of an .ics file as
        a astring, generate/yield VEVENT component objects

    get_event_url() - given a VEVENT from Groups.io, extract the subgroup
        name and event ID and use them to assemble the Groups.io peramlink

    get_ical_contents() - given an ical file, load the contents as a string

    get_calendar_contents() - given a URL for an .ics file, return
        the contents of the .ics file as a string

    get_safe_event_id() - Groups.io uses email addresses for their Event IDs,
        but Google calendar is more strict. This strips non-alphanumeric characters
        from Groups.io event IDs to make them safe for Google Calendar.

    vevent_decode() - Given a VEVENT component, convert it to ical format and decode
        the resulting binary string to unicode.
"""


def export_ical_file(calendar,icsfile):
    """
    Given a Calendar() object,
    export to an .ics file at icsfile
    """
    f = open(icsfile, 'wb')
    f.write(calendar.to_ical())
    f.close()



def new_calendar_from_components_map(short_description,components_map):
    """
    Given a components map (UID -> VEVENT object),
    create a new Calendar() object populated with
    all of the events in the components_map
    """
    # Make a new calendar that compiles all events
    newcal = Calendar()
    newcal.add('prodid', '//%s//Google Calendar 70.9054//EN'%(short_description))
    newcal.add('version', '2.0')
    newcal.add('method','PUBLISH')
    newcal.add('calscale','GREGORIAN')

    for event in components_map:
        e = Event()
        
        for k in component.keys():
            v = component[k]
            e.add(k,v)
        newcal.add_component(e)

    return newcal



def ics_components_map(ics, components_map={}):
    """
    This function takes an input string containing
    the contents of an .ics file and converts it
    into a map of uid to filtered Event() objects
    (VEVENT components).
    """
    for e in ics_components_generator(ics):
        components_map[get_safe_event_id(e['UID'])] = e
    return components_map



def ics_components_generator(ics):
    """
    This function takes an input string 
    containing an .ics file and converts it
    into a stream of filtered Event() objects
    (VEVENT components).
    """
    cal = Calendar.from_ical(ics)
    for component in cal.walk():
        if component.name=='VEVENT':
            # Custom processing (extraction):
            event_url = get_event_url(component)

            e = Event()
            for k in component.keys():
                if k=='DESCRIPTION':
                    v = event_url
                else:
                    v = component[k]
                e.add(k,v)

            yield e



def get_event_url(vevent):
    """
    Given a VEVENT object, extract the subgroup name 
    and event ID from the event information provided.
    (Only works for Groups.io events!)
    """
    if vevent.name != 'VEVENT':
        err = 'Error: get_event_url() was called on something that is not a VEVENT!\n'
        err += 'Check the calling script and try again.'
        logging.error(err)
        raise Exception(err)

    # Get subgroup name from organizer
    z = vevent['ORGANIZER']
    r = re.search(r'mailto:(.*)@dcppc.groups.io',z)
    subgroup = r.group(1)

    # Get event id from UID
    u = vevent['UID']
    p = u.split('@')[0]
    event_id = p.split('.')[-1]

    # Assemble these into a URL
    event_url = 'https://dcppc.groups.io/g/%s/viewevent?eventid=%s'%(subgroup,event_id)

    return event_url




def htmlify_event_url(vevent):
    """
    Given a VEVENT object, create a permalink to it
    on groups.io and return a string of the form:

    <a href="...groupsiolink...">...groupsiolink...</a>
    """
    if vevent.name != 'VEVENT':
        err = 'Error: htmlify_event_url() was called on something that is not a VEVENT!\n'
        err += 'Check the calling script and try again.'
        logging.error(err)
        raise Exception(err)

    event_url = get_event_url(vevent)

    html = '<a href="%s">%s</a>'%(event_url,event_url)

    return html



def get_ical_contents(ics_file):
    """
    Given an .ics file, extract the contents as a string
    """
    logging.info("Extracting contents of calendar in .ics file %s"%(ics_file))
    with open(ics_file,'r') as f:
        result = f.read()
        #result = re.sub('\r\n','\n',result)
    logging.info("Done extracting contents.")
    return result



def get_calendar_contents(ics_url):
    """
    This takes a URL for an .ics calendar file
    and returns the .ics file contents as a string
    """
    url = ics_url.strip()
    logging.info("Extracting contents of calendar at URL %s"%(url))
    r = requests.get(url)

    if r.status_code==200:
    
        # If the request went okay,
        # - get the content of the ics file
        # - decode it
        # - add it to the list
        content = r.content
        try:
            result = content.decode('utf-8')
            logging.info(" [+] Success!")
            return result

        except UnicodeDecodeError:
            result = content.decode('ISO-8859-1')
            logging.info(" [+] Success!")
            return result
    else:
        logging.info(" [-] FAILED with status code %s"%(r.status_code))
        logging.info(r.content.decode('utf-8'))
        return None




def get_safe_event_id(event_id):
    """
    Groups.io uses email addresses for their Event IDs,
    but Google calendar is more strict. This strips non-alphanumeric characters
    from Groups.io event IDs to make them safe for Google Calendar.
    """
    safe_event_id = event_id
    safe_event_id = re.sub('[^a-zA-Z0-9]','',safe_event_id)
    return safe_event_id



def vevent_decode(vstr):
    """
    Given a VEVENT component, convert it to ical format and decode
    the resulting binary string to unicode.
    """
    try:
        return vstr.to_ical().decode('utf-8')
    except AttributeError:
        return vstr.decode('utf-8')

