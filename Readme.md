# Data Commons - Calendars

This repository contains scripts for combining Groups.io 
calendars into a single integrated Data Commons calendar. 

This is mainly one script that scrapes events from all the
calendar feeds and combines them into a single calendar feed.
It is meant to be run on a server or a Heroku node.

## Branches

* `master` - the master branch contains scripts for running things.

* `gh-pages` - the `gh-pages` branch contains static content hosted
  at <https://calendars.nihdatacommons.us>.

* `heroku-pages` - (does not exist yet) once the calendar service is
  deployed to Heroku, this branch will contain the content hosted by Heroku.

## Make Integrated Calendar

To make the integrated calendar .ics file, run the `make_integrated_calendar.py`
script in the `scripts/` directory:

```
python scripts/make_integrated_calendar.py
```

This will output the .ics file to `samples/integrated_calendar.ics`.


