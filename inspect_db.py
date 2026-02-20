import sqlite3
import os

db_path = 'past_questions.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    print('Tables:', cursor.fetchall())
    
    # Check questions table count
    cursor.execute('SELECT COUNT(*) FROM questions')
    print('Total questions:', cursor.fetchone()[0])
    
    # Check distinct values for filtering
    cursor.execute('SELECT DISTINCT question_type, COUNT(*) FROM questions GROUP BY question_type')
    print('Question types:', cursor.fetchall())
    
    cursor.execute('SELECT DISTINCT year, COUNT(*) FROM questions GROUP BY year')
    print('Years:', cursor.fetchall())
    
    # Sample question
    cursor.execute('SELECT * FROM questions LIMIT 1')
    print('Sample question:', cursor.fetchone())
    
    conn.close()
else:
    print('DB not found')
