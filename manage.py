#!/usr/bin/env python

import re
import sys
import textwrap
import dbutils
import sqlite3

from server import db_name, current_tournament_id


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

    team_id = args[0]
    db = sqlite3.connect(db_name)
    try:
        dbutils.add_team_to_tournament(db, current_tournament_id, team_id)
    except ValueError as e:
        print(e)
        sys.exit(-1)

    print("Successfully added team: %s" % team_id)


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
