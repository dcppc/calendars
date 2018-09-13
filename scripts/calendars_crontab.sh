#!/bin/bash
#
# Add this script to your crontab at whatever frequency
# you'd like the calendars to be updated...

CALENDARS_DIR="/home/ubuntu/calendars"

cd $CALENDARS_DIR
virtualenv vp
source vp/bin/activate
pip install -r requirements.txt
cd scripts/
python dcppc_calendar.py -u -i ics_links.txt

DONE="`date +%Y%m%d_%H%M%S`"
touch /tmp/calendars_done_${DONE}

