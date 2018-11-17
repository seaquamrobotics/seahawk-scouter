#TODO:
# -Skills scouter
# -Detailed robot info
# -Robot photo upload/viewer
# -Advanced auton scouter (could be used for skills)
# -Back buttons

from flask import Flask, Markup, render_template, request
from bs4 import BeautifulSoup
from datetime import datetime
import requests
import sqlite3
import time
import csv
import os

# Configuration
current_tournament_id = 5643
current_year = 18
db_name = 'vex_turning_point' #os.environ['DB_NAME']

# Open database connection
db = sqlite3.connect(db_name)

clean = str.maketrans('', '', """ ^$#@~`&;:|{()}[]<>+=!?.,\/*-_"'""")
sanitize = str.maketrans('', '', """^~`;:|{()}[]+=\*_"'""")

def csv_output(tournament_id):
	db = sqlite3.connect(db_name)
	c = db.cursor()
	c.execute('SELECT team_name, color, side, auton_score, auton_high_flags, auton_low_flags, auton_high_caps, auton_low_caps, auton_park, driver_score, driver_high_flags, driver_low_flags, driver_high_caps, driver_low_caps, driver_park, note FROM Reports WHERE tournament_id=' + str(tournament_id))
	robotData = c.fetchall()
	c.close()
	with open('scouting.csv', 'w', newline='') as csvfile:
		csvwriter = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
		csvwriter.writerow(["tournament_id","team_name","color","side","auton_score","auton_high_flags","auton_low_flags","auton_high_caps","auton_low_caps","auton_park","driver_score","driver_high_flags","driver_low_flags","driver_high_caps","driver_low_caps","driver_park","note"])
		for row in robotData:
			csvwriter.writerow(row)

def get_tournament_info(tournament_id):
	# Scrape tournament data from vexdb.io
	# If the website layout changes I may need to rewrite the parsing
	r = requests.get('https://vexdb.io/events/view/RE-VRC-'+str(current_year)+'-'+str(tournament_id))
	parsed_html = BeautifulSoup(r.text, 'lxml')

	# Get competing teams
	teams = ''
	for x in parsed_html.find_all('td', attrs={'class': 'number'}):
		teams += x.get_text() + ' '
	teams = teams[:-1] # Remove the extra space off the end

	# Get tournament name
	tournament_name = parsed_html.find('h2').get_text()

	return teams, tournament_name

def report(reporter_ip, team_name, color, side, 
		   auton_score, auton_high_flags, auton_low_flags, auton_high_caps, auton_low_caps, auton_park,
		   driver_score, driver_high_flags, driver_low_flags, driver_high_caps, driver_low_caps,
		   driver_park, note=""):
    db = sqlite3.connect(db_name)
    c = db.cursor()
    
    time_stamp = int(time.time())
    c.execute('INSERT INTO Reports VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
          	[current_tournament_id, reporter_ip, time_stamp,
          	team_name, color, side,
          	auton_score, auton_high_flags, auton_low_flags, auton_high_caps, auton_low_caps, auton_park,
          	driver_score, driver_high_flags, driver_low_flags, driver_high_caps, driver_low_caps,
          	driver_park, note]
          	)
    
    c.close()
    db.commit()

def pull_reports(tournament_id, team_name=None):
    db = sqlite3.connect(db_name)
    c = db.cursor()

    if team_name:
        c.execute('SELECT * FROM Reports WHERE team_name="' + team_name + '" AND tournament_id=' + str(tournament_id))
    else:
        c.execute('SELECT * FROM Reports WHERE tournament_id=' + str(tournament_id))
    return c.fetchall()

def get_unscouted_robots(tournament_id): # Returns a list of unscouted robots
	db = sqlite3.connect(db_name)
	c = db.cursor()
	scouted = []
	unscouted = []
	c.execute('SELECT team_list FROM Tournaments WHERE tournament_id=' + str(tournament_id))
	teams = c.fetchall()[0][0].split()
	for r in pull_reports(tournament_id):
		for t in teams:
			if t == r[0] and t not in scouted:
				scouted.append(t)
	for r in teams:
		if r not in scouted:
			unscouted.append(r)
	c.close()
	return unscouted

def compress_reports(tournament_id): # Compile data and find average values for each robot
    db = sqlite3.connect(db_name)
    c = db.cursor()
    c.execute('SELECT team_name, auton_score, driver_score, note FROM Reports WHERE tournament_id=' + str(tournament_id))
    robotData = c.fetchall()
    robots = []
    for row in robotData:  # Find unique robots
        if row[0] not in robots: robots.append(row[0])
    compressedData = []
    for robot in robots:
        best_drive_score = 0
        best_auton_score = 0
        total_drive_score = 0
        total_auton_score = 0
        entryCount = 0
        notes = ''
        for row in robotData:
            if row[0] == robot:
                entryCount += 1
                total_drive_score += int(row[2])
                total_auton_score += int(row[1])
                if int(row[2]) > best_drive_score:
                	best_drive_score = int(row[2])
                if int(row[1]) > best_auton_score:
                	best_auton_score = int(row[1])
                if row[3]:
                	notes += '~ '+row[3]+'<br>'
        compressedData.append([robot, best_drive_score, int(total_drive_score / entryCount), best_auton_score, int(total_auton_score / entryCount), notes, entryCount])
    c.close()
    return compressedData


def robot_power(robot_stats): # Enter compiled data row as input. Formula: power = best_driver + avg_driver + best_auton + avg_auton + highest_stack * 2 + times_scouted
	power = 0
	for i, s in enumerate(robot_stats[1:]):
		if i != 4:
			power += int(s)
	return power

def reverse_bubble_sort(collection): # Sort reports by best robot power
	length = len(collection)
	for i in range(length-1, -1, -1):
		for j in range(i):
			if robot_power(collection[j]) > robot_power(collection[j+1]):
				collection[j], collection[j+1] = collection[j+1], collection[j]
	return collection[::-1]


app = Flask(__name__)

@app.route('/') # Home page
def index():
	db = sqlite3.connect(db_name)
	c = db.cursor()
	c.execute('SELECT tournament_name FROM Tournaments WHERE tournament_id=' + str(current_tournament_id))
	tournament_name = c.fetchall()[0][0]
	return render_template('index.html', current_tournament_name=tournament_name, current_tournament_id=current_tournament_id, status="Seaquam Robotics Scouting")

@app.route('/scouting', methods=['POST', 'GET']) # Scouting submission page
def scouting():
	#TODO: Store diffent autonomous positions
	if request.method == 'POST':
		db = sqlite3.connect(db_name)
		c = db.cursor()
		c.execute('SELECT tournament_name, team_list FROM Tournaments WHERE tournament_id=' + str(current_tournament_id))
		query = c.fetchall()
		c.close()
		tournament_name = query[0][0]
		valid_teams = query[0][1].split()
		auton_score = 0
		score = 0
		team_name = request.form['team'].translate(clean).upper()
		if team_name in valid_teams:
			print("Report submitted for " + team_name)

			color = request.form.get('color', '')
			side = request.form.get('side', '')
			auton_park_string = request.form.get('auton_park', '')
			driver_park_string = request.form.get('driver_park', '')


			reporter_ip = request.environ['REMOTE_ADDR'].translate(clean)

			
			auton_low_flags = int(request.form['auton_low_flags'])
			auton_high_flags = int(request.form['auton_high_flags'])
			auton_low_caps = int(request.form['auton_low_caps'])
			auton_high_caps = int(request.form['auton_high_caps'])
			auton_park = 0
			if auton_park_string == 'alliance':
				auton_park = 3
			elif auton_park_string == 'none':
				auton_park = 0
			auton_score += auton_low_flags + auton_high_flags * 2 + auton_low_caps + auton_high_caps * 2 + auton_park
			print(auton_score)
			
			driver_low_flags = int(request.form['driver_low_flags'])
			driver_high_flags = int(request.form['driver_high_flags'])
			driver_low_caps = int(request.form['driver_low_caps'])
			driver_high_caps = int(request.form['driver_high_caps'])

			driver_park = 0
			if driver_park_string == 'high':
				driver_park = 6
			elif driver_park_string == 'alliance':
				driver_park = 3
			else:
				driver_park = 0

			driver_score = driver_low_flags + driver_high_flags * 2 + driver_low_caps + driver_high_caps * 2 + driver_park

			print(driver_score)

			note = request.form['notes'].translate(sanitize)


			report(reporter_ip, team_name, color, side, 
				auton_score, auton_high_flags, auton_low_flags, auton_high_caps, auton_low_caps, auton_park,
				driver_score, driver_high_flags, driver_low_flags, driver_high_caps, driver_low_caps,
				driver_park, note)

		else:
			if len(team_name) == 0:
				team_name = "NULL"
			return render_template('index.html', current_tournament_name=tournament_name, current_tournament_id=current_tournament_id, status=Markup('<span class="error">Error:</span> Invalid team name: ' + team_name + " not found in list of participating robots."))
		return render_template('index.html', current_tournament_name=tournament_name, current_tournament_id=current_tournament_id, status="Scouting report sent successfully")
	elif request.method == 'GET':
		return render_template('scouting.html')

@app.route('/data/<int:tournament_id>') # Compiled scouting reports page
def data(tournament_id):
	db = sqlite3.connect(db_name)
	c = db.cursor()
	c.execute('SELECT tournament_name FROM Tournaments WHERE tournament_id=' + str(tournament_id))
	tournament_name = c.fetchall()[0][0]
	c.close()
	robots_data = ''
	for i, row in enumerate(reverse_bubble_sort(compress_reports(tournament_id))): 
		robots_data += '<tr><td>'+str(i+1)+'</td>'
		for i, cell in enumerate(row):
			if i == 0:
				robots_data += '<td><a href="../autonomous/'+str(cell)+'">'+str(cell)+'</a></td>'
			else:
				robots_data += '<td>'+str(cell)+'</td>'
		robots_data +='</tr>'
	robots_data_html = Markup(robots_data)

	unscouted_robots = get_unscouted_robots(tournament_id)
	unscouted = ''
	if unscouted_robots:
		unscouted += '<h2>Not Yet Scouted:</h2><div class="unscouted">'
	else:
		unscouted = '<h2>All Robots Scouted</h2>'
	for r in unscouted_robots:
		unscouted += r+' '
	unscouted_html = Markup(unscouted+'</div>')

	return render_template('data.html', tournament_name=tournament_name, data=robots_data_html, unscouted=unscouted_html)

@app.route('/tournaments')
def tournaments():
	db = sqlite3.connect(db_name)
	c = db.cursor()
	tournaments_html = ''
	c.execute('SELECT tournament_id, tournament_name, team_list FROM Tournaments')
	for t in c.fetchall():
		tournaments_html += '<a class="box2 bluebg" href="data/' + str(t[0]) + '">' + t[1] + '</a>'
	tournaments_html = Markup(tournaments_html)
	c.close()
	return render_template('past_tournaments.html', tournaments=tournaments_html)

@app.route('/autonomous/<string:team_name>') # Show all autonomous attempt details for a specified team
def autonomous(team_name):
	autonomous_reports = ''
	db = sqlite3.connect(db_name)
	c = db.cursor()
	c.execute('SELECT auton_score, color, side, time_stamp FROM Reports WHERE team_name="' + team_name + '" AND tournament_id=' + str(current_tournament_id))
	for row in c.fetchall():
		classes = ''
		if row[1] == 'red': classes = 'redteam '
		elif row[1] == 'blue': classes = 'blueteam '
		else: classes = 'noteam '

		side = ''
		if row[2] == 'right': 
			side = 'RIGHT'
		elif row[2] == 'left': 
			side = 'LEFT'
		else: 
			side = '?????'

		autonomous_reports += '<div class="'+classes+'box2"><span class="left">' + datetime.fromtimestamp(row[3]).strftime('%I:%M %p') + '</span>' + str(row[0]) + ' Points <span class="right">' + side + ' TILE</span></div>'
	c.close()
	autonomous_reports = Markup(autonomous_reports)
	return render_template('autonomous.html', team_name=team_name.upper(), autonomous_reports=autonomous_reports)

@app.route("/upload", methods=['POST', 'GET'])
def upload():
	return render_template('upload.html')
    #uploaded_files = flask.request.files.getlist("file[]")
    #print(uploaded_files)
    #return "Your files have been uploaded"

#@app.route('/delete') # Page for deleting incorrect scouting reports
#ef delete():
#	reporter_ip = request.environ['REMOTE_ADDR'].translate(clean)
#	reports_html = ''
#	c.execute('SELECT team_name, auton_score, driver_score, highest_stack, notes, time_stamp FROM Reports WHERE reporter_ip=' + str(reporter_ip))
#	for row in c.fetchall():
#		reports_html += '<div class="box2 bluebg">' + str(row[0]) + '</div>'
#
#	return render_template('delete.html', reports=reports_html)

@app.route('/agenda')
def agenda():
	return render_template('agenda.html')

@app.errorhandler(404) # Error 404 page
def page_not_found(e):
	return render_template('404.html'), 404

if __name__ == '__main__':
	csv_output(current_tournament_id)
	# Create tables if they do not already exist
	#c.execute('SHOW TABLES')
	tbls = []#str(c.fetchall())
	if True:#'Tournaments' not in tbls:
		c = db.cursor()
		c.execute('CREATE TABLE IF NOT EXISTS Tournaments(tournament_id INT, tournament_name TEXT, team_list TEXT, PRIMARY KEY (tournament_id))')
		c.close()
		db.commit()
	if True:#'Reports' not in tbls:
		c = db.cursor()
		c.execute('CREATE TABLE IF NOT EXISTS Reports(tournament_id INT, reporter_ip BIGINT, timestamp BIGINT, team_name TEXT, color TEXT, side TEXT, auton_score INT, auton_high_flags INT, auton_low_flags INT, auton_high_caps INT, auton_low_caps INT, auton_park INT, driver_score INT, driver_high_flags INT, driver_low_flags INT, driver_high_caps INT, driver_low_caps INT, driver_park INT, note TEXT)')
		c.close()
		db.commit()
	
	# If current tournament does not exist in Tournaments table then add it
	c = db.cursor()
	c.execute('SELECT * FROM Tournaments WHERE tournament_id=' + str(current_tournament_id))
	if len(c.fetchall()) == 0:

		teams, tournament_name = get_tournament_info(current_tournament_id)

		# Make new tournament entry
		c.execute('INSERT INTO Tournaments(tournament_id, tournament_name, team_list)' +
                  'VALUES ('+str(current_tournament_id)+',"'+tournament_name+'","'+teams+'")')
		c.close()
		db.commit()

	app.run(threaded=True, debug=True, host='0.0.0.0', port=8000)

db.close()