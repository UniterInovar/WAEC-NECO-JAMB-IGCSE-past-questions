import sqlite3
import os

def verify():
    conn = sqlite3.connect('past_questions.db')
    cursor = conn.cursor()
    
    # 1. Check for question_type consistency
    cursor.execute('SELECT DISTINCT question_type FROM questions')
    types = cursor.fetchall()
    print(f"Detected Types in DB: {types}")
    
    # 2. Verify some questions have years
    cursor.execute('SELECT COUNT(*) FROM questions WHERE year IS NOT NULL')
    year_count = cursor.fetchone()[0]
    print(f"Questions with Year: {year_count}")
    
    # 3. Simulate filter query
    subject = 'biology'
    exam_type = 'jamb'
    cursor.execute(f"SELECT DISTINCT year FROM questions WHERE subject LIKE '{subject}' AND exam_type LIKE '{exam_type}'")
    years = cursor.fetchall()
    print(f"Years for {subject}/{exam_type}: {years}")

    conn.close()

if __name__ == "__main__":
    verify()
