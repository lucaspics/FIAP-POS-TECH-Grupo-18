import sqlite3

# connect to the database
conn = sqlite3.connect('database/data.db')
cursor = conn.cursor()

# Create a table
cursor.execute('''
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    screen_path TEXT NOT NULL,
    incident TEXT NOT NULL,
    timestamp DATETIME NOT NULL
)
''')

conn.commit()
conn.close()