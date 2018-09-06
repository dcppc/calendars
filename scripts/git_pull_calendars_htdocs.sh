#!/bin/bash
#
# This pulls the latest changes
# in from the gh-pages branch
# of dcppc/calendars

git -C /www/calendars.nihdatacommons.us \
    --git-dir=git --work-tree=htdocs \
    pull origin gh-pages

