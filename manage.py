#!/usr/bin/env python

import csv
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


def dump_csv(*args):
	doc = textwrap.dedent("""
	Usage: ./manage.py dumpcsv [optional tournament_id]
	
	Dumps all scouting data for a given tournament ID to a CSV file.
	""").strip()

	if len(args) == 0:
		tournament_id = current_tournament_id
	elif args[0].lower() == "help":
		print(doc)
		sys.exit(0)
	else:
		tournament_id = args[0]

	db = sqlite3.connect(db_name)
	c = db.cursor()
	c.execute(
		'SELECT team_name, color, side, auton_score, auton_high_flags, auton_low_flags, auton_high_caps, '
		'auton_low_caps, auton_park, driver_score, driver_high_flags, driver_low_flags, driver_high_caps, '
		'driver_low_caps, driver_park, note FROM Reports WHERE tournament_id=?', (str(tournament_id),))

	robot_data = c.fetchall()
	c.close()

	csvwriter = csv.writer(sys.stdout, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
	csvwriter.writerow(
		["tournament_id", "team_name", "color", "side", "auton_score", "auton_high_flags", "auton_low_flags",
		 "auton_high_caps", "auton_low_caps", "auton_park", "driver_score", "driver_high_flags", "driver_low_flags",
		 "driver_high_caps", "driver_low_caps", "driver_park", "note"])
	for row in robot_data:
		csvwriter.writerow(row)


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
	elif sys.argv[1] == "dumpcsv":
		dump_csv(*sys.argv[2:])
	else:
		print(doc)
