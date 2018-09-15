# NIH Data Commons Pilot Phase: The Calendars Page

This repository contains scripts for combining Groups.io 
calendars into a single integrated Data Commons calendar
on Google Calendar.

See <https://calendars.nihdatacommons.us>!

This is mainly one script that scrapes events from all the
calendar feeds and combines them into a single Google Calendar.
It is meant to be run on a server or a Heroku node.

## Branches

* `master` - the master branch contains scripts for running things.

* `gh-pages` - the `gh-pages` branch contains static content hosted
  at <https://calendars.nihdatacommons.us>.

* `heroku-pages` - (does not exist yet) once the calendar service is
  deployed to Heroku, this branch will contain the content hosted by Heroku.

## Make integrated Google Calendar

The user needs to enable the Google Calendar API for whatever account they're 
going to create DCPPC events on, and they need to create an OAuth app, and 
they need to obtain the API credentials for their OAuth app from the Google 
Cloud console. This is the `client_secret.json` file. 

The uesr can then authenticate with the app using their Google account (whichever 
account should have the events added to its calendar). The user can run the
Google Calendar authentication script, which will open a browser locally and
ask them to log in via Google and grant permission for the OAuth app to modify
their calendar. Once the user grants the application permission, they will be
given a `credentials.json` file to download. This `credentials.json` file is
what is required to run the DCPPC calendars script.

TODO: Add a Google Calendar authentication script.

To make the integrated Google Calendar, run the `dcppc_calendar.py`
script in the `scripts/` directory:

```
$ python scripts/dcppc_calendar.py -h
usage: dcppc_calendar.py [-h] [-c] [-u] -i ICAL_LIST [-f] [-n NAME]

This script creates/updates an integrated calendar of DCPPC events. Pass
either the --create or --update flag. The --ical-list flag is required and
should point to a file with one .ics URL per line.The --name flag is optional.

optional arguments:
  -h, --help            show this help message and exit
  -c, --create          (REQUIRED, use one of -c or -u) Create a new Google
                        Calendar with integrated calendar events
  -u, --update          (REQUIRED, use one of -c or -u) Update (sync) an
                        existing Google Calendar with integrated calendar
                        events
  -i ICAL_LIST, --ical-list ICAL_LIST
                        (REQUIRED) Name of a file containing a list of
                        Groups.io .ics URLs, one per line
  -f, --force-sync      (OPTIONAL, use with -u) Force every event on the
                        calendar to synchronize, regardless of whether there
                        are changes.
  -n NAME, --name NAME  (OPTIONAL) Name of the calendar ("DCPPC Calendar" by
                        default)
```

You should either create or update a calendar (use `-c` or `-u`).

You should pass the name of the calendar you want to create with the script
using the `-n` flag (optional, "DCPPC Calendar" by default).

You should pass a list of .ical files, one URL per line, using the `-i` flag.

If you have made modifications to the way that the calendar descriptions are
constructed, or some other aspect of how ical events are converted to Google 
Calendar events, you may want to force each event to be synchronized. You can
do that using the `-f` flag.

## Google Calendar API sample scripts

See the `api_gcal/` directory for scripts containing examples of interacting
with the Google Calendar API.

## Deploy gh-pages branch to calendars.nihdatacommons.us

To deploy the `gh-pages` branch to the live site at <https://calendars.nihdatacommons.us>,
we `git clone` the `gh-pages` branch in such a way that the
contents of the branch (the static content that should be
hosted by nginx) is stored separate from the contents of 
the `.git` directory (which should not be hosted by nginx).

To clone the repo with this directory structure, use the
wrapper script in `scripts/git_clone_calendars_htdocs.sh`,
which clones the `gh-pages` branch of this repo to 
`/www/calendars.nihdatacommons.us/`, storing the repo content
(the `gh-pages` branch) ain the `htdocs/` directory and the
contents of what would otherwise be the `.git` directory in the
repo in the `git/` directory.

To update the repo with the latest changes to the `gh-pages`
branch, run `git pull` using the wrapper script in
`script/git_pull_calendars_htdocs.sh`.

