class Tournament:
    def __init__(self, **kwargs):
        self.tournament_id = kwargs.get("tournament_id")
        self.tournament_name = kwargs.get("tournament_name")
        self.team_list = kwargs.get("team_list")


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
        return Tournament(tournament_id=r[0], tournament_name=r[1], team_list=r[2])
    else:
        return None


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
