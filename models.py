import sqlite3
from contextlib import contextmanager

PYQ_DB = 'pyq_weightage.db'
REV_WEIGHTAGE_DB = 'revision_weightage.db'
TIMETABLE_DB = 'created_timetable.db'
REV_TIMETABLE_DB = 'revision_timetable.db'

@contextmanager
def get_db_connection(db_file):
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def get_all_subjects_pyq():
    with get_db_connection(PYQ_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM subject_weightage")
        return [dict(row) for row in cursor.fetchall()]

def get_all_subjects_revision():
    with get_db_connection(REV_WEIGHTAGE_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM revision_weightage")
        return [dict(row) for row in cursor.fetchall()]

def create_timetable_entry(name, description):
    with get_db_connection(TIMETABLE_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Timetables (timetable_name, description) VALUES (?, ?)", (name, description))
        conn.commit()
        return cursor.lastrowid

def insert_timetable_slots(slots, timetable_id):
    """
    slots: list of dicts with keys: slot_date, start_time, end_time, subject
    """
    with get_db_connection(TIMETABLE_DB) as conn:
        cursor = conn.cursor()
        # We use executemany for efficiency
        data = [(timetable_id, s['date'], s['start_time'], s['end_time'], s['subject']) for s in slots]
        cursor.executemany('''
            INSERT INTO TimetableSlots (timetable_id, slot_date, start_time, end_time, subject)
            VALUES (?, ?, ?, ?, ?)
        ''', data)
        conn.commit()

def create_rev_timetable_entry(name, description):
    with get_db_connection(REV_TIMETABLE_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Revision_Timetables (rev_timetable_name, description) VALUES (?, ?)", (name, description))
        conn.commit()
        return cursor.lastrowid

def insert_rev_timetable_slots(slots, rev_timetable_id):
    """
    slots: list of dicts with keys: slot_date, start_time, end_time, subject
    """
    with get_db_connection(REV_TIMETABLE_DB) as conn:
        cursor = conn.cursor()
        data = [(rev_timetable_id, s['date'], s['start_time'], s['end_time'], s['subject']) for s in slots]
        cursor.executemany('''
            INSERT INTO TimetableSlots (rev_timetable_id, slot_date, start_time, end_time, subject)
            VALUES (?, ?, ?, ?, ?)
        ''', data)
        conn.commit()
