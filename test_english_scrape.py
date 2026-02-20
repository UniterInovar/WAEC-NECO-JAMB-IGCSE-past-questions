from scrapers.myschool_scraper import MySchoolScraper
import json

def test_english_scrape():
    scraper = MySchoolScraper()
    # Find English Language URL
    subjects = scraper.scrape_subjects()
    english_url = None
    for s in subjects:
        if "English" in s['name']:
            english_url = s['url']
            break
    
    if not english_url:
        print("English Language not found in subjects.")
        return

    print(f"Testing scrape for English Language ({english_url})...")
    
    # Scrape 5 questions to see varieties
    results = scraper.scrape_questions(english_url, limit=5, min_year=2020, exam_type='jamb')
    
    print(f"Scraped {len(results)} questions.")
    for i, r in enumerate(results):
        print(f"\n--- Question {i+1} ---")
        print(f"URL: {r['source_url']}")
        print(f"Body Type: {type(r['body'])}")
        print(f"Body: {r['body']}")
        print(f"Options: {r['options']}")
        print(f"Explanation Type: {type(r['explanation'])}")
        print(f"Explanation: {repr(r['explanation'])}")

if __name__ == "__main__":
    test_english_scrape()
