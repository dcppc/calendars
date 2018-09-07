from icalendar import Calendar, Event
import re, os
import requests



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
    This function takes an input string  containing
    the contents of an .ics file and converts it
    into a map of uid to filtered Event() objects
    (VEVENT components).
    """
    for e in ics_component_generator(ics):
        components_map[e['UID']] = e
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


def get_calendar_contents(ics_url):
    """
    This takes a URL for an .ics calendar file
    and returns the .ics file contents as a string
    """
    url = ics_url.strip()
    print("Adding calendar %s to integrated calendar"%(url))
    r = requests.get(url)

    if r.status_code==200:
    
        # If the request went okay,
        # - get the content of the ics file
        # - decode it
        # - add it to the list
        content = r.content
        try:
            result = content.decode('utf-8')
            result = re.sub('\r\n','\n',result)
            print(" [+] Success!")

            return result

        except UnicodeDecodeError:
            # We need to figure out what to do here.
            # utf-16 results in chinese characters!!
            #####result = content.decode('utf-16')
            #####result = re.sub('\r\n','\n',result)
            #####calendar_contents.append(result)
            #####print(" [+] Success!")
            #
            ## This is useful for printing what characters are weird
            #import unicodedata
            #for c in r.text:
            #    if ord(c) >= 127:
            #        print('{} U+{:04x} {}'.format(c.encode('utf8'), ord(c), unicodedata.name(c)))
            #print(" [-] FAILED but printed useful information")
            #
            print(" [-] FAIL")
            return None
    else:
        print(" [-] FAILED with status code %s"%(r.status_code))
        print(r.content.decode('utf-8'))
        return None





