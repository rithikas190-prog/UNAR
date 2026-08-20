import sqlite3
import json
import os
import uuid

DATA_DIR = os.environ.get("RENDER_DATA_DIR", os.path.dirname(__file__))
DB_PATH = os.path.join(DATA_DIR, "unar_data.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Interviews table
    c.execute('''
        CREATE TABLE IF NOT EXISTS interviews (
            id TEXT PRIMARY KEY,
            candidate_name TEXT,
            candidate_role TEXT,
            start_time TEXT,
            end_time TEXT,
            status TEXT
        )
    ''')
    
    # Assessments table (stores the huge JSON)
    c.execute('''
        CREATE TABLE IF NOT EXISTS assessments (
            interview_id TEXT PRIMARY KEY,
            data TEXT,
            FOREIGN KEY(interview_id) REFERENCES interviews(id)
        )
    ''')
    conn.commit()
    conn.close()

def create_interview(interview_id: str, candidate_name: str, candidate_role: str, start_time: str) -> str:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO interviews (id, candidate_name, candidate_role, start_time, status) VALUES (?, ?, ?, ?, ?)",
        (interview_id, candidate_name, candidate_role, start_time, "active")
    )
    conn.commit()
    conn.close()
    return interview_id

def update_interview_status(interview_id: str, status: str, end_time: str = None):
    conn = get_connection()
    c = conn.cursor()
    if end_time:
        c.execute("UPDATE interviews SET status = ?, end_time = ? WHERE id = ?", (status, end_time, interview_id))
    else:
        c.execute("UPDATE interviews SET status = ? WHERE id = ?", (status, interview_id))
    conn.commit()
    conn.close()

def save_assessment(interview_id: str, data: dict):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO assessments (interview_id, data) VALUES (?, ?)",
        (interview_id, json.dumps(data))
    )
    conn.commit()
    conn.close()

def get_assessment(interview_id: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT data FROM assessments WHERE interview_id = ?", (interview_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return json.loads(row["data"])
    return None

def get_interview(interview_id: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM interviews WHERE id = ?", (interview_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

init_db()
