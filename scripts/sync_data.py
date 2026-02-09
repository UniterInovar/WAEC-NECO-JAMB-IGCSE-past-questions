import requests
import sys
import os
import json

# Add parent directory to path to import scrapers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.myschool_scraper import MySchoolScraper

def sync():
    # Configuration
    DEFAULT_URL = "https://waec-neco-jamb-igcse-past-questions.onrender.com"
    
    print("=== MySchool Local Sync Tool ===")
    print("This tool scrapes questions using your local internet and pushes them to Render.")
    print("-" * 30)

    # 0. Verify URL
    remote_url_input = input(f"Enter your Render URL (default: {DEFAULT_URL}): ").strip()
    REMOTE_URL = remote_url_input if remote_url_input else DEFAULT_URL
    
    if REMOTE_URL.endswith('/'):
        REMOTE_URL = REMOTE_URL[:-1]

    print(f"\nTesting connection to {REMOTE_URL}...")
    try:
        # Check if server is alive and has the bulk endpoint
        test_resp = requests.get(f"{REMOTE_URL}/myschool-subjects")
        if test_resp.status_code == 200:
            print("Successfully connected to Remote Server!")
        else:
            print(f"Server returned status {test_resp.status_code}. Please verify the URL above is correct.")
            return
    except Exception as e:
        print(f"Error: Could not connect to {REMOTE_URL}. {e}")
        return

    # 1. Input parameters
    subject_query = input("\nEnter Subject Name (e.g., Biology): ").strip()
    exam_type = input("Enter Exam Type (jamb/waec/neco): ").strip().lower()
    limit = int(input("Enter max questions to scrape (default 50): ") or 50)
    
    scraper = MySchoolScraper()
    
    # 2. Get Subject URL
    print("\nFetching subject list from scraper...")
    subjects = scraper.scrape_subjects()
    subject_url = None
    subject_name = None
    for s in subjects:
        if s['name'].lower() == subject_query.lower():
            subject_url = s['url']
            subject_name = s['name']
            break
            
    if not subject_url:
        print(f"Error: Subject '{subject_query}' not found. Check subjects.json for valid names.")
        return

    # 3. Get Existing URLs from Remote to avoid duplicates
    print(f"Checking existing questions on remote server for {subject_name}...")
    try:
        resp = requests.get(f"{REMOTE_URL}/questions?subject={subject_name.lower()}")
        if resp.status_code == 200:
            existing_questions = resp.json()
            existing_urls = [q['source_url'] for q in existing_questions if q.get('source_url')]
            print(f"Found {len(existing_urls)} existing questions on remote.")
        else:
            existing_urls = []
    except Exception:
        existing_urls = []

    # 4. Scrape Locally
    print(f"\nScraping {subject_name} ({exam_type}) locally...")
    scraped_data = scraper.scrape_questions(
        subject_url, 
        limit=limit, 
        min_year=2000, 
        existing_urls=existing_urls, 
        exam_type=exam_type
    )

    if not scraped_data:
        print("No new questions found. All questions might already be on the server.")
        return

    print(f"\nSuccessfully scraped {len(scraped_data)} new questions.")
    
    # 5. Push to Remote
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
            print(f"Success! Server message: {sync_resp.json().get('message')}")
            print("Refresh your website dashboard to see the new questions.")
        else:
            print(f"Error {sync_resp.status_code}: {sync_resp.text}")
    except Exception as e:
        print(f"Upload failed: {e}")

if __name__ == "__main__":
    sync()
