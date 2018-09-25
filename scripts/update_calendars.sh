#!/bin/bash
#
# Add this script to your crontab at whatever frequency
# you'd like the calendars to be updated...

CALENDARS_DIR="/home/ubuntu/calendars"
DONE="`date +%Y%m%d_%H%M%S`"

cd $CALENDARS_DIR
virtualenv vp
source vp/bin/activate
pip install -r requirements.txt
cd scripts/
python dcppc_calendar.py -u -i ics_links.txt &> /tmp/calendars_done_${DONE}

