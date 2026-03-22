import sqlite3
import json

DB_PATH = 'bot_cache.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Force alignment by dropping any legacy mismatched tables
    cursor.execute("DROP TABLE IF EXISTS file_cache")
    cursor.execute("DROP TABLE IF EXISTS search_cache")
    
    cursor.execute('''CREATE TABLE file_cache (
        video_id TEXT PRIMARY KEY, 
        file_id TEXT, 
        title TEXT, 
        artist TEXT, 
        duration INTEGER
    )''')
    cursor.execute('''CREATE TABLE search_cache (
        query TEXT PRIMARY KEY, 
        results TEXT
    )''')
    conn.commit()
    conn.close()

def save_file_id(video_id, file_id, title, artist, duration):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO file_cache VALUES (?, ?, ?, ?, ?)', (video_id, file_id, title, artist, duration))
    conn.commit()
    conn.close()

def get_file_cache(video_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT file_id, title, artist, duration FROM file_cache WHERE video_id = ?', (video_id,))
    row = cursor.fetchone()
    conn.close()
    return {'file_id': row[0], 'title': row[1], 'artist': row[2], 'duration': row[3]} if row else None

def save_search(query, results):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO search_cache VALUES (?, ?)', (query.lower(), json.dumps(results)))
    conn.commit()
    conn.close()

def get_search(query):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT results FROM search_cache WHERE query = ?', (query.lower(),))
    row = cursor.fetchone()
    conn.close()
    return json.loads(row[0]) if row else None
