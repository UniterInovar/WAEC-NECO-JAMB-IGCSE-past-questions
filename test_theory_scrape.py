from scrapers.myschool_scraper import MySchoolScraper

def test_theory_practical_scrape():
    scraper = MySchoolScraper()
    subject_url = "https://myschool.ng/classroom/biology"
    
    # Test Theory for 2024 WAEC
    print("\n--- Testing Theory Scraping (Biology 2024 WAEC) ---")
    theory_questions = scraper.scrape_questions(
        subject_url, 
        limit=5, 
        min_year=2024, 
        max_year=2024, 
        exam_type='waec', 
        question_type='theory'
    )
    
    print(f"Scraped {len(theory_questions)} theory questions.")
    for i, q in enumerate(theory_questions):
        print(f"\n[Question {i+1}] Type: {q['question_type']}")
        print(f"Body: {q['body'][:200]}...")
        print(f"Options Count: {len(q['options'])}")
        print(f"URL: {q['source_url']}")

    # Test Practical for 2024 WAEC
    # (Note: scrape_questions should handle practical if theory is requested)
    print("\n--- Testing Practical Scraping (Biology 2024 WAEC) ---")
    # Note: Our internal logic says if type='theory', it checks both theory and practical
    practical_questions = scraper.scrape_questions(
        subject_url, 
        limit=5, 
        min_year=2024, 
        max_year=2024, 
        exam_type='waec', 
        question_type='practical' 
    )
    
    print(f"Scraped {len(practical_questions)} practical questions.")
    for i, q in enumerate(practical_questions):
        print(f"\n[Practical {i+1}] Type: {q['question_type']}")
        print(f"Body: {q['body'][:200]}...")

if __name__ == "__main__":
    test_theory_practical_scrape()
