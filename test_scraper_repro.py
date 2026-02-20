from scrapers.myschool_scraper import MySchoolScraper
import json

def test_biology_scrape():
    scraper = MySchoolScraper()
    subject_url = "https://myschool.ng/classroom/biology"
    subject_name = "Biology"
    
    print(f"Testing scrape for {subject_name} ({subject_url})...")
    
    # Test with WAEC first as we saw it has data
    print("\n--- Test 1: WAEC filter (Limit 2) ---")
    results_waec = scraper.scrape_questions(subject_url, limit=2, min_year=2020, exam_type='waec')
    print(f"Scraped {len(results_waec)} WAEC questions.")
    if results_waec:
        for r in results_waec:
            print(f"- {r['exam_type']} ({r['year']}): {r['body'][:50]}...")
    
    # Test with JAMB
    print("\n--- Test 2: JAMB filter (Limit 2) ---")
    results_jamb = scraper.scrape_questions(subject_url, limit=2, min_year=2020, exam_type='jamb')
    print(f"Scraped {len(results_jamb)} JAMB questions.")

if __name__ == "__main__":
    test_biology_scrape()
