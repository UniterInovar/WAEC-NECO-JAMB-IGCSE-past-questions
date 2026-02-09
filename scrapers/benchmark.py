import sys
import os
import time
sys.path.append(os.getcwd())
from scrapers.myschool_scraper import MySchoolScraper

def benchmark():
    s = MySchoolScraper()
    print("Starting benchmark (5 questions)...")
    start = time.time()
    questions = s.scrape_questions('https://myschool.ng/classroom/biology', limit=5)
    end = time.time()
    
    print(f"\nScraped {len(questions)} questions in {end-start:.2f} seconds.")
    
    for i, q in enumerate(questions):
        has_img = '<img' in q['body'] or any('<img' in opt for opt in q['options'])
        print(f"Q{i+1}: {q['body'][:50]}... (Image: {has_img})")
        if has_img:
            # Extract and print img tag for verification
            img_match = re.search(r'<img[^>]+>', q['body'])
            if img_match:
                print(f"  Img tag: {img_match.group(0)}")

if __name__ == "__main__":
    import re
    benchmark()
