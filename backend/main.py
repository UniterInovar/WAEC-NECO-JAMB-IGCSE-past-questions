from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, aloc_client
from .models import SessionLocal, engine, Question, init_db
from pydantic import BaseModel
from typing import List, Optional
import sys
import os

# Add parent directory to path to import scrapers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.myschool_scraper import MySchoolScraper

init_db()

app = FastAPI(title="Past Questions API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionSchema(BaseModel):
    id: int
    body: str
    options: Optional[List[str]]
    answer: str
    explanation: Optional[str]
    subject: str
    year: Optional[int]
    exam_type: str
    topic: Optional[str]
    source_url: Optional[str]

    model_config = {
        "from_attributes": True
    }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/seed-mock")
def seed_mock(db: Session = Depends(get_db)):
    mock_questions = [
        {
            "body": "What is the capital of Nigeria?",
            "options": ["Lagos", "Abuja", "Kano", "Ibadan"],
            "answer": "Abuja",
            "explanation": "Abuja became the capital of Nigeria in 1991, replacing Lagos.",
            "subject": "Government",
            "year": 2023,
            "exam_type": "jamb"
        },
        {
            "body": "Which of these is responsible for carrying oxygen in the blood?",
            "options": ["White blood cells", "Platelets", "Red blood cells", "Plasma"],
            "answer": "Red blood cells",
            "explanation": "Hemoglobin in red blood cells binds to oxygen and carries it through the body.",
            "subject": "Biology",
            "year": 2022,
            "exam_type": "waec"
        }
    ]
    
    for q_data in mock_questions:
        exists = db.query(Question).filter(Question.body == q_data['body']).first()
        if not exists:
            new_q = Question(**q_data)
            db.add(new_q)
    
    db.commit()
    return {"message": "Database seeded with mock questions"}

@app.get("/questions", response_model=List[QuestionSchema])
def read_questions(subject: Optional[str] = None, year: Optional[int] = None, exam_type: Optional[str] = None, topic: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Question)
    if subject:
        query = query.filter(Question.subject.ilike(subject))
    if year:
        query = query.filter(Question.year == year)
    if exam_type:
        query = query.filter(Question.exam_type.ilike(exam_type))
    if topic:
        query = query.filter(Question.topic.ilike(topic))
    return query.all()

@app.get("/filters")
def get_filters(db: Session = Depends(get_db)):
    # Use distinct and cast to lower/case-insensitive where possible
    subjects = db.query(Question.subject).distinct().all()
    years = db.query(Question.year).distinct().all()
    topics = db.query(Question.topic).distinct().all()
    
    # Handle duplicates and case sensitivity in Python for simplicity
    unique_subjects = sorted(list(set(s[0].capitalize() for s in subjects if s[0])))
    unique_years = sorted([y[0] for y in years if y[0]], reverse=True)
    unique_topics = sorted(list(set(t[0] for t in topics if t[0])))
    
    return {
        "subjects": unique_subjects,
        "years": unique_years,
        "topics": unique_topics
    }

@app.get("/fetch-aloc")
def fetch_aloc(subject: str, db: Session = Depends(get_db)):
    client = aloc_client.ALOCClient()
    data = client.get_multiple_questions(subject)
    if not data or 'data' not in data:
        raise HTTPException(status_code=400, detail="Failed to fetch data from ALOC")
    
    questions_added = 0
    for q_data in data['data']:
        exists = db.query(Question).filter(Question.body == q_data['question']).first()
        if not exists:
            options = [q_data['option']['a'], q_data['option']['b'], q_data['option']['c'], q_data['option']['d']]
            if 'e' in q_data['option']:
                options.append(q_data['option']['e'])
            
            new_q = Question(
                body=q_data['question'],
                options=options,
                answer=q_data['answer'],
                explanation=q_data.get('solution'),
                subject=subject,
                year=int(q_data['examyear']) if q_data.get('examyear') else None,
                exam_type=q_data.get('examtype', 'jamb'),
                topic="General"
            )
            db.add(new_q)
            questions_added += 1
    
    db.commit()
    return {"message": f"Added {questions_added} questions for {subject}"}

@app.get("/myschool-subjects")
def get_myschool_subjects():
    scraper = MySchoolScraper()
    return scraper.scrape_subjects()

@app.get("/clear-questions")
def clear_questions(db: Session = Depends(get_db)):
    db.query(Question).delete()
    db.commit()
    return {"message": "All questions have been deleted from the database"}

@app.get("/scrape/myschool")
def scrape_myschool(subject_url: str, subject_name: str, limit: int = 20, min_year: int = 2000, exam_type: Optional[str] = None, db: Session = Depends(get_db)):
    scraper = MySchoolScraper()
    
    # Get existing source_urls to skip them in the scraper
    existing_urls = [q.source_url for q in db.query(Question.source_url).all() if q.source_url]
    
    scraped_data = scraper.scrape_questions(subject_url, limit=limit, min_year=min_year, existing_urls=existing_urls, exam_type=exam_type)
    
    questions_added = 0
    for q_data in scraped_data:
        # Final safety check against duplicates
        exists = db.query(Question).filter(Question.source_url == q_data['source_url']).first()
        if not exists:
            new_q = Question(
                body=q_data['body'],
                options=q_data['options'],
                answer=q_data['answer'],
                explanation=q_data['explanation'],
                subject=subject_name,
                year=q_data['year'],
                exam_type=q_data['exam_type'],
                topic=q_data.get('topic', 'General'),
                source_url=q_data['source_url']
            )
            db.add(new_q)
            questions_added += 1
    
    db.commit()
    return {"message": f"Scraped and added {questions_added} questions for {subject_name} (Year {min_year}+)"}

@app.get("/")
def root():
    return {"message": "Welcome to the Past Questions API"}
