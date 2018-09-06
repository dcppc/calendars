#!/bin/bash
#
# This clones dcppc/calendars with a
# directory structure that allows the
# static content and the .git directory
# to live in separate places.
#
# use the git_pull_calendar_htdocs.sh script
# to pull the latest changes correctly
# with this weird directory structure.

REPOURL="git@github.com:dcppc/calendars"

git -C /www/calendars.nihdatacommons.us \
    clone \
    --separate-git-dir=git \
    -b gh-pages \
    $REPOURL htdocs

