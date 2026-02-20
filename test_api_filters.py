from fastapi.testclient import TestClient
from backend.main import app
from backend.models import SessionLocal, Question, engine, Base

# Setup test DB
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_filtering():
    # Clear and Seed
    db = SessionLocal()
    db.query(Question).delete()
    
    q1 = Question(
        body="Q1 Obj 2023",
        subject="biology",
        year=2023,
        exam_type="jamb",
        question_type="objective",
        answer="A"
    )
    q2 = Question(
        body="Q2 Theory 2023",
        subject="biology",
        year=2023,
        exam_type="jamb",
        question_type="theory",
        answer="B"
    )
    q3 = Question(
        body="Q3 Obj 2022",
        subject="biology",
        year=2022,
        exam_type="jamb",
        question_type="objective",
        answer="C"
    )
    db.add(q1)
    db.add(q2)
    db.add(q3)
    db.commit()
    
    print("\n--- Test 1: Filter by Year 2023 ---")
    resp = client.get("/questions?subject=biology&exam_type=jamb&year=2023")
    print(f"Status: {resp.status_code}, Found: {len(resp.json())}")
    for q in resp.json():
        print(f"  - {q['body']} ({q['question_type']})")
        
    print("\n--- Test 2: Filter by Type theory ---")
    resp = client.get("/questions?subject=biology&exam_type=jamb&question_type=theory")
    print(f"Status: {resp.status_code}, Found: {len(resp.json())}")
    for q in resp.json():
        print(f"  - {q['body']} (Year: {q['year']})")

    print("\n--- Test 3: Filter by Both (2023 + objective) ---")
    resp = client.get("/questions?subject=biology&exam_type=jamb&year=2023&question_type=objective")
    print(f"Status: {resp.status_code}, Found: {len(resp.json())}")
    for q in resp.json():
        print(f"  - {q['body']}")

if __name__ == "__main__":
    test_filtering()
