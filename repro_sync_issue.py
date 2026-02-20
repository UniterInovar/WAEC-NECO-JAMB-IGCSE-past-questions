from scrapers.myschool_scraper import MySchoolScraper
import os
import json

def repro():
    scraper = MySchoolScraper()
    subject_url = "https://myschool.ng/classroom/biology"
    etype = "waec"
    year = 2024
    qtype = "theory"
    
    print(f"DEBUG: Starting repro for {etype} {year} {qtype}")
    
    # Mimic sync_data.py's call
    year_data = scraper.scrape_questions(
        subject_url, 
        limit=5, 
        min_year=year, 
        max_year=year, 
        existing_urls=[], 
        exam_type=etype,
        question_type=qtype
    )
    
    print(f"DEBUG: Found {len(year_data)} questions.")
    if year_data:
        for q in year_data:
            print(f" - [{q['year']}] {q['question_type']} : {q['source_url']}")
    else:
        print("DEBUG: year_data is EMPTY.")

if __name__ == "__main__":
    repro()
