from sqlalchemy import Column, Integer, String, Text, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    body = Column(Text, nullable=False)
    options = Column(JSON)  # Store options as a JSON array or dict
    answer = Column(String(500))
    explanation = Column(Text)
    subject = Column(String(100))
    year = Column(Integer)
    exam_type = Column(String(50)) # jamb, waec, neco, nabteb, igcse
    topic = Column(String(200))
    source_url = Column(String(500), unique=True, index=True)

engine = create_engine('sqlite:///./past_questions.db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
