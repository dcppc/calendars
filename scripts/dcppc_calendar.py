import sys
import argparse

def main():
    args = parse_args()

def parse_args():
    """
    Parse the user arguments
    """

    descr = "This script creates/updates an integrated calendar of DCPPC events. "
    descr += "Pass either the --create or --update flag. "
    descr += "The --name flag is optional."

    parser = argparse.ArgumentParser(description=descr)
    parser.add_argument(
            '-c', '--create', 
            action='store_true',
            help='(REQUIRED) Create a new Google Calendar with integrated calendar events'
    )
    parser.add_argument(
            '-u', '--update', 
            action='store_true',
            help='(REQUIRED) Update (sync) an existing Google Calendar with integrated calendar events'
    )
    parser.add_argument(
            '-n', '--name', 
            default = "DCPPC Calendar",
            help='(OPTIONAL) Name of the calendar ("DCPPC Calendar" by default)'
    )
    args = parser.parse_args()

    if args.create:
        print("Creating calendar \"%s\""%args.name)
    elif args.update:
        print("Updating calendar \"%s\""%args.name)
    else:
        parser.print_help(sys.stderr)

if __name__=="__main__":
    main()

