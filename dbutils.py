class Tournament:
	def __init__(self, **kwargs):
		self.tournament_id = kwargs.get("tournament_id")
		self.tournament_name = kwargs.get("tournament_name")
		self.team_list = kwargs.get("team_list")

	@staticmethod
	def from_db_row(cur, row):
		return Tournament(**_get_row_dict(cur, row))


class Report:
	def __init__(self, **kwargs):
		self.tournament_id = kwargs.get("tournament_id")
		self.reporter_ip = kwargs.get("reporter_ip")
		self.team_name = kwargs.get("team_name")
		self.color = kwargs.get("color")
		self.side = kwargs.get("side")
		self.auton_score = kwargs.get("auton_score")
		self.auton_low_flags = kwargs.get("auton_low_flags")
		self.auton_high_flags = kwargs.get("auton_high_flags")
		self.auton_low_caps = kwargs.get("auton_low_caps")
		self.auton_high_caps = kwargs.get("auton_high_caps")
		self.auton_park = kwargs.get("auton_park")
		self.driver_score = kwargs.get("driver_score")
		self.driver_low_flags = kwargs.get("driver_low_flags")
		self.driver_high_flags = kwargs.get("driver_high_flags")
		self.driver_low_caps = kwargs.get("driver_low_caps")
		self.driver_high_caps = kwargs.get("driver_high_caps")
		self.driver_park = kwargs.get("driver_park")
		self.note = kwargs.get("note")
		self.timestamp = kwargs.get("time_stamp")

	@staticmethod
	def from_db_row(cur, row):
		return Report(**_get_row_dict(cur, row))


def create_db_tables(db):
	"""Creates the necessary database tables if they don't already exist.
	:param db Database connection object
	"""
	c = db.cursor()

	c.execute("""
		CREATE TABLE IF NOT EXISTS Tournaments(
			tournament_id INT, 
			tournament_name TEXT, 
			team_list TEXT, 
			PRIMARY KEY (tournament_id))
	""")

	c.execute("""
		CREATE TABLE IF NOT EXISTS Reports(
			tournament_id INT, 
			reporter_ip BIGINT, 
			timestamp BIGINT, 
			team_name TEXT, 
			color TEXT, 
			side TEXT, 
			auton_score INT, 
			auton_high_flags INT, 
			auton_low_flags INT, 
			auton_high_caps INT, 
			auton_low_caps INT, 
			auton_park INT, 
			driver_score INT, 
			driver_high_flags INT, 
			driver_low_flags INT, 
			driver_high_caps INT, 
			driver_low_caps INT, 
			driver_park INT, 
			note TEXT)
	""")

	db.commit()


def get_all_tournaments(db):
	"""Gets all tournaments in the database
	:param db Database connection object
	:return List of tournament objects
	"""
	c = db.cursor()
	c.execute("SELECT * FROM Tournaments")
	return [Tournament.from_db_row(c, row) for row in c]


def get_tournament_by_id(db, tournament_id):
	"""Gets tournament information from the database.
	:param db Database connection object
	:param tournament_id Tournament ID
	:return Tournament object or None if not found
	"""
	c = db.cursor()
	c.execute('SELECT * FROM Tournaments WHERE tournament_id=?', (tournament_id,))
	r = c.fetchone()

	if r is not None:
		return Tournament.from_db_row(c, r)
	else:
		return None


def get_reports_for_tournament(db, tournament_id, team_id=None):
	"""Gets all reports for a tournament
	:param db Database connection object
	:param tournament_id Tournament id
	:param team_id Filter for team ID (optional)
	:return List of Report objects
	"""
	c = db.cursor()
	if team_id is None:
		res = c.execute("SELECT * FROM Reports WHERE tournament_id=?", (tournament_id,))
	else:
		res = c.execute("SELECT * FROM Reports WHERE tournament_id=? AND team_name=?",
						(tournament_id, team_id))
	return [Report.from_db_row(c, row) for row in res]


def create_tournament(db, tournament_info):
	"""Creates a new tournament entry.
	:param db Database connection object
	:param tournament_info Tournament object
	"""
	c = db.cursor()
	c.execute("""
		INSERT INTO Tournaments(tournament_id, tournament_name, team_list)
		VALUES (?, ?, ?)
	""", (tournament_info.tournament_id, tournament_info.tournament_name, tournament_info.team_list))

	db.commit()


def create_report(db, tournament_id, report_info):
	c = db.cursor()

	c.execute('INSERT INTO Reports VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (
				tournament_id,
				report_info.reporter_ip,
				report_info.timestamp,
				report_info.team_name,
				report_info.color,
				report_info.side,
				report_info.auton_score,
				report_info.auton_high_flags,
				report_info.auton_low_flags,
				report_info.auton_high_caps,
				report_info.auton_low_caps,
				report_info.auton_park,
				report_info.driver_score,
				report_info.driver_high_flags,
				report_info.driver_low_flags,
				report_info.driver_high_caps,
				report_info.driver_low_caps,
				report_info.driver_park,
				report_info.note)
			)

	db.commit()


def _get_row_dict(cur, row):
	# Weird hacky way of converting a sqlite row into a dictionary.
	d = {}
	for i, column in enumerate(cur.description):
		d[column[0]] = row[i]
	return d
