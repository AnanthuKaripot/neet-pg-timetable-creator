import sqlite3
import os

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Exception as e:
        print(e)
    return conn

def init_pyq_weightage_db():
    database = "pyq_weightage.db"
    conn = create_connection(database)
    if conn is not None:
        cursor = conn.cursor()
        # Create table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subject_weightage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_name TEXT NOT NULL,
                weightage INTEGER NOT NULL
            );
        ''')
        
        # Initial Data
        subjects = [
            ("Anatomy", 7), ("Physiology", 7), ("Biochemistry", 13),
            ("Pathology", 14), ("Pharmacology", 14), ("Microbiology", 12),
            ("Forensic Medicine", 9), ("Community Medicine", 15),
            ("General Medicine", 21), ("General Surgery", 23), ("Obstetrics & Gynae", 19),
            ("Pediatrics", 9), ("Orthopaedics", 6), ("Ophthalmology", 8), ("ENT", 7),
            ("Dermatology", 5), ("Radiology", 4), ("Anaesthesiology", 4), ("Psychiatry", 4)
        ]
        
        # Check if empty
        cursor.execute("SELECT count(*) FROM subject_weightage")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("INSERT INTO subject_weightage (subject_name, weightage) VALUES (?, ?)", subjects)
            print(f"Populated {database}")
            
        conn.commit()
        conn.close()
    else:
        print(f"Error! cannot create the database connection to {database}")

def init_revision_weightage_db():
    database = "revision_weightage.db"
    conn = create_connection(database)
    if conn is not None:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS revision_weightage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_name TEXT NOT NULL,
                weightage INTEGER NOT NULL
            );
        ''')
        
        subjects = [
            ("Anatomy", 7), ("Physiology", 7), ("Biochemistry", 13),
            ("Pathology", 14), ("Pharmacology", 14), ("Microbiology", 12),
            ("Forensic Medicine", 9), ("Community Medicine", 15),
            ("General Medicine", 21), ("General Surgery", 23), ("Obstetrics & Gynae", 19),
            ("Pediatrics", 9), ("Orthopaedics", 6), ("Ophthalmology", 8), ("ENT", 7),
            ("Dermatology", 5), ("Radiology", 4), ("Anaesthesiology", 4), ("Psychiatry", 4)
        ]
        
        cursor.execute("SELECT count(*) FROM revision_weightage")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("INSERT INTO revision_weightage (subject_name, weightage) VALUES (?, ?)", subjects)
            print(f"Populated {database}")

        conn.commit()
        conn.close()
    else:
        print(f"Error! cannot create the database connection to {database}")

def init_created_timetable_db():
    database = "created_timetable.db"
    conn = create_connection(database)
    if conn is not None:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Timetables (
                timetable_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timetable_name VARCHAR(255) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS TimetableSlots (
                slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timetable_id INTEGER NOT NULL,
                slot_date DATE NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                subject TEXT,
                FOREIGN KEY (timetable_id) REFERENCES Timetables(timetable_id),
                UNIQUE (timetable_id, slot_date, start_time)
            );
        ''')
        conn.commit()
        conn.close()
        print(f"Initialized {database}")

def init_revision_timetable_db():
    database = "revision_timetable.db"
    conn = create_connection(database)
    if conn is not None:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Revision_Timetables (
                rev_timetable_id INTEGER PRIMARY KEY AUTOINCREMENT,
                rev_timetable_name VARCHAR(255) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS TimetableSlots (
                slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                rev_timetable_id INTEGER NOT NULL,
                slot_date DATE NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                subject TEXT,
                FOREIGN KEY (rev_timetable_id) REFERENCES Revision_Timetables(rev_timetable_id),
                UNIQUE (rev_timetable_id, slot_date, start_time)
            );
        ''')
        conn.commit()
        conn.close()
        print(f"Initialized {database}")

if __name__ == '__main__':
    init_pyq_weightage_db()
    init_revision_weightage_db()
    init_created_timetable_db()
    init_revision_timetable_db()
