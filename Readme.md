# NIH Data Commons Pilot Phase: The Calendars Page

This repository contains scripts for combining Groups.io 
calendars into a single integrated Data Commons calendar. 

See <https://calendars.nihdatacommons.us>!

This is mainly one script that scrapes events from all the
calendar feeds and combines them into a single calendar feed.
It is meant to be run on a server or a Heroku node.

## Branches

* `master` - the master branch contains scripts for running things.

* `gh-pages` - the `gh-pages` branch contains static content hosted
  at <https://calendars.nihdatacommons.us>.

* `heroku-pages` - (does not exist yet) once the calendar service is
  deployed to Heroku, this branch will contain the content hosted by Heroku.

## Make integrated calendar .ics file

To make the integrated calendar .ics file, run the `make_integrated_calendar.py`
script in the `scripts/` directory:

```
python scripts/make_integrated_cal.py
```

For testing, you can output the .ics file to samples; for the real deal,
the calendar file is deployed to the `htdocs/` directory.

## Google Calendar API sample scripts

See the `api_gcal/` directory for scripts containing examples of interacting
with the Google Calendar API. These will eventually be used to assemble a
Google Calendar script in the `scripts/` folder.

## Deploy gh-pages branch to calendars.nihdatacommons.us

To deploy the `gh-pages` branch to the live site at <https://calendars.nihdatacommons.us>,
we `git clone` the `gh-pages` branch in such a way that the
contents of the branch (the static content that should be
hosted by nginx) is stored separate from the contents of 
the `.git` directory (which should not be hosted by nginx).

To clone the repo with this directory structure, use the
`git_clone_calendars_htdocs.sh` script, which clones to
`/www/calendars.nihdatacommons.us/` and stores the static
content in `htdocs/` and the `.git` directory at `git/`.

To update the repo with the latest changes to the `gh-pages`
branch, run `git pull` using the wrapper script,
`git_pull_calendars_htdocs.sh`.


