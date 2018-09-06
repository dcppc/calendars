from icalendar import Calendar, Event
import re, os
import requests

# ahhhhh
# https://icalendar.org/validator.html

SCRIPT_DIR = os.path.split(os.path.abspath(__file__))[0]

ICSLINKS_DIR = os.path.join(SCRIPT_DIR,'..')
ICSLINKS_FILE = 'ics_links.txt'

HTDOCS_DIR = '/www/calendars.nihdatacommons.us/htdocs'

### # Test
### ICS_DIR = os.path.join(SCRIPT_DIR,'..','samples')
# Real deal
ICS_DIR = os.path.join(HTDOCS_DIR,'..','samples')
# Leave this alone
ICS_FILE = 'integrated_calendar.ics'

def main():

    # Get list of ics URLs
    icsfile = os.path.join(ICSLINKS_DIR,ICSLINKS_FILE)
    with open(icsfile,'r') as f:
        urls = f.readlines()
    
    # Scrape contents of ics file and add to list
    calendar_contents = []
    for url in urls:
        url = url.strip()
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
                calendar_contents.append(result)
                print(" [+] Success!")
            except UnicodeDecodeError:
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
        else:
            print(" [-] FAILED with status code %s"%(r.status_code))
            print(r.content.decode('utf-8'))
    

    newcal = Calendar()
    newcal.add('prodid', '//DCPPC//Google Calendar 70.9054//EN')
    newcal.add('version', '2.0')
    newcal.add('method','PUBLISH')
    newcal.add('calscale','GREGORIAN')

    for calendar in calendar_contents:
        cal = Calendar.from_ical(calendar)
        for component in cal.walk():
            if component.name=='VEVENT':
                e = Event()
                # 
                # If we want to do custom processing,
                # do it here.
                #
                # Extract the subgroup and event ID
                # from the UID field. Format is:
                # UID:calendar.9284.327237@groups.io
                #                   ^^^^^^
                #                   event id
                # 
                # Turn into a URL as follows:
                # https://dcppc.groups.io/g/kc6tech/viewevent?eventid=327237
                # 
                for k in component.keys():
                    v = component[k]
                    e.add(k,v)
                newcal.add_component(e)

    icsfile = os.path.join(ICS_DIR,ICS_FILE)
    f = open(icsfile, 'wb')
    f.write(newcal.to_ical())
    f.close()

if __name__=="__main__":
    main()
