#!/usr/bin/env python

import sys
import textwrap


def add_team(*args):
    doc = textwrap.dedent("""
    Usage: ./manage.py addteam [team_id]

    Adds a team to the current tournament.    
    
    Arguments:
        team_id: VRC team number to add
    """).strip()

    if len(args) == 0:
        print(doc)
        sys.exit(-1)


if __name__ == "__main__":
    doc = textwrap.dedent("""
    Usage: ./manage.py [command]
        
    Management tasks for the scouting database.
    """).strip()

    # Check length of arguments
    if len(sys.argv) <= 1:
        print(doc)
        sys.exit(-1)

    if sys.argv[1] == "addteam":
        add_team(*sys.argv[2:])
    else:
        print(doc)
