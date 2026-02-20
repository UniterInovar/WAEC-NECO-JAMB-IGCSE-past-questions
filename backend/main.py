from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
    id: Optional[int] = None
    body: str
    options: Optional[List[str]]
    answer: str
    explanation: Optional[str]
    subject: str
    year: Optional[int]
    exam_type: str
    question_type: str = "objective"
    topic: Optional[str] = "General"
    source_url: Optional[str] = None

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
def read_questions(subject: Optional[str] = None, year: Optional[int] = None, exam_type: Optional[str] = None, question_type: Optional[str] = None, topic: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Question)
    if subject:
        query = query.filter(Question.subject.ilike(subject))
    if year:
        query = query.filter(Question.year == year)
    if exam_type:
        query = query.filter(Question.exam_type.ilike(exam_type))
    if question_type:
        query = query.filter(Question.question_type.ilike(question_type))
    if topic:
        query = query.filter(Question.topic.ilike(topic))
    return query.all()

@app.get("/filters")
def get_filters(subject: Optional[str] = None, exam_type: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Question)
    if subject:
        query = query.filter(Question.subject.ilike(subject))
    if exam_type:
        query = query.filter(Question.exam_type.ilike(exam_type))
    
    # Use distinct values from the filtered query
    subjects = db.query(Question.subject).distinct().all() # Keep all subjects available for selection
    years = query.with_entities(Question.year).distinct().all()
    topics = query.with_entities(Question.topic).distinct().all()
    q_types = query.with_entities(Question.question_type).distinct().all()
    
    # Handle duplicates and case sensitivity in Python
    unique_subjects = sorted(list(set(s[0].capitalize() for s in subjects if s[0])))
    unique_years = sorted([y[0] for y in years if y[0]], reverse=True)
    unique_topics = sorted(list(set(t[0] for t in topics if t[0])))
    unique_types = sorted(list(set(qt[0].lower() for qt in q_types if qt[0])))
    
    return {
        "subjects": unique_subjects,
        "years": unique_years,
        "topics": unique_topics,
        "question_types": unique_types
    }

@app.get("/fetch-aloc")
def fetch_aloc(subject: str, count: int = 50, db: Session = Depends(get_db)):
    print(f"DEBUG: ALOC fetch request for {subject}. Count: {count}")
    
    # Check for token first
    if not os.getenv("ALOC_TOKEN"):
        raise HTTPException(
            status_code=401, 
            detail="ALOC Access Token is missing. Please set the ALOC_TOKEN in your environment variables."
        )

    client = aloc_client.ALOCClient()
    data = client.get_multiple_questions(subject, count=count)
    if not data or 'data' not in data:
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to fetch data from ALOC. Error: {data.get('error') if data else 'Unknown'}"
        )
    
    questions_added = 0
    for q_data in data['data']:
        # Double check for existing body to avoid duplicates
        exists = db.query(Question).filter(Question.body == q_data['question']).first()
        if not exists:
            options = [q_data['option']['a'], q_data['option']['b'], q_data['option']['c'], q_data['option']['d']]
            if 'e' in q_data['option'] and q_data['option']['e']:
                options.append(q_data['option']['e'])
            
            new_q = Question(
                body=q_data['question'],
                options=options,
                answer=q_data['answer'].upper() if q_data.get('answer') else 'A',
                explanation=q_data.get('solution'),
                subject=subject.lower(),
                year=int(q_data['examyear']) if q_data.get('examyear') and str(q_data['examyear']).isdigit() else None,
                exam_type=q_data.get('examtype', 'jamb').lower(),
                question_type='objective', # ALOC is almost exclusively objective
                topic="General"
            )
            db.add(new_q)
            questions_added += 1
    
    db.commit()
    return {"message": f"Added {questions_added} questions for {subject} using ALOC source."}

@app.post("/questions/bulk")
def bulk_upload_questions(questions: List[QuestionSchema], db: Session = Depends(get_db)):
    print(f"DEBUG: Bulk upload request for {len(questions)} questions.")
    added_count = 0
    for q_data in questions:
        # Avoid duplicates by body and metadata OR source_url
        exists = db.query(Question).filter(
            (Question.source_url == q_data.source_url if q_data.source_url else False) | 
            (
                (Question.body == q_data.body) & 
                (Question.subject == q_data.subject.lower()) & 
                (Question.year == q_data.year) & 
                (Question.exam_type == q_data.exam_type.lower())
            )
        ).first()
        
        if not exists:
            new_q = Question(
                body=q_data.body,
                options=q_data.options,
                answer=q_data.answer,
                explanation=q_data.explanation,
                subject=q_data.subject.lower(),
                year=q_data.year,
                exam_type=q_data.exam_type.lower(),
                question_type=q_data.question_type.lower(),
                topic=q_data.topic or "General",
                source_url=q_data.source_url
            )
            db.add(new_q)
            added_count += 1
    
    db.commit()
    return {"message": f"Bulk upload complete. Added {added_count} new questions."}

@app.get("/myschool-subjects")
def get_myschool_subjects():
    scraper = MySchoolScraper()
    return scraper.scrape_subjects()

@app.get("/clear-questions")
def clear_questions(db: Session = Depends(get_db)):
    db.query(Question).delete()
    db.commit()
    return {"message": "All questions have been deleted from the database"}

@app.post("/scrape/myschool")
def scrape_myschool(
    subject: str, 
    exam_type: Optional[str] = "jamb", 
    year: Optional[int] = None, 
    limit: Optional[int] = 50,
    question_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    scraper = MySchoolScraper()
    subject_url = f"{scraper.base_url}/classroom/{subject.lower().replace(' ', '-')}"
    
    # Get existing URLs to avoid duplicates
    existing_urls = [q.source_url for q in db.query(Question).filter(Question.subject == subject.lower()).all() if q.source_url]
    
    questions = scraper.scrape_questions(
        subject_url, 
        limit=limit, 
        min_year=year if year else 2000, 
        max_year=year if year else None,
        existing_urls=existing_urls,
        exam_type=exam_type,
        question_type=question_type
    )
    # Check if we were likely blocked
    # We can check a flag or just assume based on 0 results if we saw 403 in inner logs
    # To be precise, let's look at the result count and the fact that we confirmed blocking
    if not questions:
        # We need a way for the scraper to communicate the block back up.
        # For now, if it's 0 and we are on Render, it's almost certainly a block.
        # Let's check status_code from a dummy request
        test_resp = scraper.session.get(subject_url, headers=scraper.headers, timeout=5)
        if test_resp.status_code == 403:
            raise HTTPException(
                status_code=403, 
                detail="MySchool is blocking this server's IP address (Cloudflare). Please use the ALOC source for ingestion."
            )

    print(f"DEBUG: Scraper returned {len(scraped_data)} results.")
    
    questions_added = 0
    for q_data in scraped_data:
        # Final safety check against duplicates
        exists = db.query(Question).filter(
            (Question.source_url == q_data['source_url']) |
            (
                (Question.body == q_data['body']) & 
                (Question.subject == subject_name.lower()) & 
                (Question.year == q_data['year']) & 
                (Question.exam_type == q_data['exam_type'].lower())
            )
        ).first()
        if not exists:
            new_q = Question(
                body=q_data['body'],
                options=q_data['options'],
                answer=q_data['answer'],
                explanation=q_data['explanation'],
                subject=subject_name,
                year=q_data['year'],
                exam_type=q_data['exam_type'],
                question_type=q_data.get('question_type', 'objective'),
                topic=q_data.get('topic', 'General'),
                source_url=q_data['source_url']
            )
            db.add(new_q)
            questions_added += 1
    
    db.commit()
    return {"message": f"Scraped and added {questions_added} questions for {subject_name} (Year {min_year}+)"}

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "message": "Past Questions API is running"}

# Mount frontend static files
# This should be at the end to avoid intercepting API routes
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
