#!/usr/bin/env python

import csv
import sys
import textwrap
import dbutils
import sqlite3
import requests

from server import db_name, current_tournament_id, current_year


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


def import_tournament(*args):
	doc = textwrap.dedent("""
		Usage: ./manage.py importtournament [csv file] [tournament id]

		Imports tournament team data from a csv file
		""").strip()

	if len(args) == 2:
		csv_path = args[0]
		tournament_id = args[1]
	elif len(args) == 1:
		csv_path = args[0]
		tournament_id = current_tournament_id
	else:
		print(doc)
		sys.exit(0)

	# Get tournament name
	print("Looking for tournament %s on vexdb..." % tournament_id)
	resp = requests.get("http://api.vexdb.io/v1/get_events?sku=RE-VRC-%d-%d"
						% (current_year, tournament_id)).json()
	if resp["size"] > 0:
		name = resp["result"][0]["name"]
		print("Found tournament: %s" % name)
	else:
		print("Couldn't find tournament!")
		sys.exit(-1)

	with open(csv_path, 'r') as file:
		reader = csv.reader(file)
		next(reader)  # skip first row

		team_list = [row[0] for row in reader]
		teams = " ".join(team_list)

	db = sqlite3.connect(db_name)
	dbutils.create_tournament(db, dbutils.Tournament(
		tournament_id=tournament_id,
		tournament_name=name,
		team_list=teams
	))

	print("Added %d teams to the database." % len(team_list))


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
	elif sys.argv[1] == "importtournament":
		import_tournament(*sys.argv[2:])
	else:
		print(doc)
