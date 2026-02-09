import sqlite3
import os

db_path = 'past_questions.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(questions)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'source_url' not in columns:
            cursor.execute('ALTER TABLE questions ADD COLUMN source_url VARCHAR(500)')
            cursor.execute('CREATE UNIQUE INDEX idx_questions_source_url ON questions (source_url)')
            conn.commit()
            print('Migration successful: source_url added.')
        else:
            print('Migration skipped: source_url already exists.')
    except Exception as e:
        print(f'Migration error: {e}')
    finally:
        conn.close()
else:
    print('Database not found, init_db will handle it.')
