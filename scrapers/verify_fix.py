import sys
import os
import re
sys.path.append(os.getcwd())
from scrapers.myschool_scraper import MySchoolScraper

def test_extraction():
    s = MySchoolScraper()
    # Let's test a page that likely has topics and potentially images
    url = 'https://myschool.ng/classroom/biology'
    print(f"Testing extraction from {url}...")
    questions = s.scrape_questions(url, limit=5)
    
    if not questions:
        print("No questions found.")
        return

    print(f"Fetched {len(questions)} questions.")
    for i, q in enumerate(questions):
        has_img = '<img' in q['body'] or any('<img' in opt for opt in q['options'])
        print(f"\nQ{i+1}: Topic: {q['topic']} | Year: {q['year']} | Source: {q['source_url']}")
        print(f"   Body Length: {len(q['body'])}")
        print(f"   Body Preview: {q['body'][:200]}...")
        print(f"   Image found: {has_img}")
        if has_img:
            img_tag = re.search(r'<img[^>]+>', q['body'])
            if img_tag:
                 print(f"   Img tag: {img_tag.group(0)}")

if __name__ == "__main__":
    test_extraction()
