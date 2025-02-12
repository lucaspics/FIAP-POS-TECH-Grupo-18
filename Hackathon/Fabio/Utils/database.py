import sqlite3
from datetime import datetime

# connect to the database
conn = sqlite3.connect('database/data.db', check_same_thread=False)
cursor = conn.cursor()

# Create a table
def create_table():
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        screen_path TEXT NOT NULL,
        incident TEXT NOT NULL,
        timestamp DATETIME NOT NULL
    )
    ''')
    conn.commit()

def insert_incident(screenshot, incident):
    cursor.execute("INSERT INTO messages (screen_path, incident, timestamp) VALUES (?, ?, ?)",
                       (screenshot, incident, datetime.now()))
    conn.commit()

def get_incidents():
    cursor.execute('SELECT * FROM messages ORDER BY timestamp DESC')
    messages = cursor.fetchall()
    return messages

def delete_incident(id):
    cursor.execute("DELETE FROM messages WHERE id = ?", (id,))
    conn.commit()
