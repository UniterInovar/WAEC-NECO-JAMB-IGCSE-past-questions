import requests
import sys
import os
import json

# Add parent directory to path to import scrapers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.myschool_scraper import MySchoolScraper

def sync():
    # Configuration
    REMOTE_URL = "https://waec-neco-jamb-igcse-past-questions.onrender.com" # Default from your repo name
    
    print("=== MySchool Local Sync Tool ===")
    print(f"Target Server: {REMOTE_URL}")
    print("-" * 30)

    # Input parameters
    subject_query = input("Enter Subject Name (e.g., Biology): ").strip()
    exam_type = input("Enter Exam Type (jamb/waec/neco): ").strip().lower()
    limit = int(input("Enter max questions to scrape (default 50): ") or 50)
    
    scraper = MySchoolScraper()
    
    # 1. Get Subject URL
    print("\nFetching subject list...")
    subjects = scraper.scrape_subjects()
    subject_url = None
    for s in subjects:
        if s['name'].lower() == subject_query.lower():
            subject_url = s['url']
            subject_name = s['name']
            break
            
    if not subject_url:
        print(f"Error: Subject '{subject_query}' not found. Check subjects.json for valid names.")
        return

    # 2. Get Existing URLs from Remote to avoid duplicates
    print(f"Checking existing questions on remote server...")
    try:
        # We'll fetch all questions to get their source URLs
        resp = requests.get(f"{REMOTE_URL}/questions?subject={subject_name.lower()}")
        if resp.status_code == 200:
            existing_questions = resp.json()
            existing_urls = [q['source_url'] for q in existing_questions if q.get('source_url')]
            print(f"Found {len(existing_urls)} existing questions on remote.")
        else:
            print("Warning: Could not fetch existing questions. Proceeding with clear list.")
            existing_urls = []
    except Exception as e:
        print(f"Connection Error: {e}")
        existing_urls = []

    # 3. Scrape Locally
    print(f"\nScraping {subject_name} ({exam_type}) locally (this bypasses Cloudflare blocks)...")
    scraped_data = scraper.scrape_questions(
        subject_url, 
        limit=limit, 
        min_year=2000, 
        existing_urls=existing_urls, 
        exam_type=exam_type
    )

    if not scraped_data:
        print("No new questions found to sync.")
        return

    print(f"\nSuccessfully scraped {len(scraped_data)} new questions.")
    
    # 4. Push to Remote
    confirm = input(f"Do you want to upload these {len(scraped_data)} questions to {REMOTE_URL}? (y/n): ")
    if confirm.lower() != 'y':
        print("Upload cancelled.")
        return

    print("Uploading to remote server...")
    try:
        # Post to the new bulk endpoint
        sync_resp = requests.post(
            f"{REMOTE_URL}/questions/bulk",
            json=scraped_data,
            headers={"Content-Type": "application/json"}
        )
        
        if sync_resp.status_code == 200:
            print(f"Success! {sync_resp.json().get('message')}")
        else:
            print(f"Error {sync_resp.status_code}: {sync_resp.text}")
    except Exception as e:
        print(f"Upload failed: {e}")

if __name__ == "__main__":
    sync()
