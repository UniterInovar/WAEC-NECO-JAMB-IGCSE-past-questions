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
    
    print("=== MySchool Local Sync Tool (v1.1) ===")
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
    print("\nSelect Data Source:")
    print("1. MySchool (Scraped from web - often blocked)")
    print("2. ALOC (Reliable API - requires ALOC_TOKEN on server)")
    source_choice = input("Choice (1 or 2, default 1): ").strip() or "1"
    
    if source_choice == "2":
        subject_query = input("\nEnter Subject Name (e.g., Chemistry): ").strip()
        count = int(input("Enter number of questions to fetch (default 50): ") or 50)
        
        print(f"\nRequesting Remote Server to fetch {count} questions for {subject_query} via ALOC...")
        try:
            resp = requests.get(f"{REMOTE_URL}/fetch-aloc?subject={subject_query.lower()}&count={count}", timeout=30)
            if resp.status_code == 200:
                print(f"Success! {resp.json().get('message')}")
            else:
                print(f"Error {resp.status_code}: {resp.json().get('detail')}")
        except Exception as e:
            print(f"Failed to trigger ALOC fetch: {e}")
        return

    subject_query = input("\nEnter Subject Name (e.g., Biology): ").strip()
    exam_type = input("Enter Exam Type (jamb/waec/neco): ").strip().lower()
    question_type = input("Enter Question Type (objective/theory, default objective): ").strip().lower() or "objective"
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
    # 3. Get Existing URLs from Remote to avoid duplicates
    print(f"Checking existing questions on remote server for {subject_name} ({question_type})...")
    try:
        remote_filter_url = f"{REMOTE_URL}/questions?subject={subject_name.lower()}&question_type={question_type}"
        resp = requests.get(remote_filter_url, timeout=15)
        if resp.status_code == 200:
            existing_questions = resp.json()
            existing_urls = [q['source_url'] for q in existing_questions if q.get('source_url')]
            print(f"Found {len(existing_urls)} existing {question_type} questions on remote.")
        else:
            print(f"Warning: Remote server returned {resp.status_code} for filter check. Assuming 0 existing.")
            existing_urls = []
    except Exception as e:
        print(f"Warning: Could not fetch existing questions from remote: {e}. Proceeding with clean scrape.")
        existing_urls = []

    # 4. Scrape Locally or Load from Cache
    print(f"\nScraping {subject_name} ({exam_type}) {question_type} locally with yearly saving...")
    
    import datetime
    current_year = datetime.datetime.now().year
    all_questions = []
    
    # Iterate through years we want to ensure we have
    found_any_matching = False
    for year in range(current_year, 1999, -1):
        if len(all_questions) >= limit:
            print(f"\nTarget limit of {limit} questions reached. Stopping scrape loop.")
            break
            
        # Partition data by subject/exam_type/year/question_type
        data_dir = os.path.join("data", subject_name.lower().replace(" ", "_"), exam_type, str(year), question_type)
        os.makedirs(data_dir, exist_ok=True)
        cache_file = os.path.join(data_dir, "questions.json")
        
        year_questions = []
        is_cached = False
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                year_questions = json.load(f)
            
            if len(year_questions) > 0:
                is_cached = True
                print(f"  Year {year}: Loaded {len(year_questions)} questions from local cache.")
            else:
                # If cached as empty, we only skip if it's an older year.
                # For recent years or if the user is explicitly trying to sync, we might want to retry.
                if year < 2010:
                    print(f"  Year {year}: Cache shows 0 questions. Skipping (use --clear to retry).")
                    continue
                else:
                    print(f"  Year {year}: Cache empty. Attempting re-scrape...")

        if not is_cached:
            print(f"  Year {year}: Scraping MySchool...")
            year_data = scraper.scrape_questions(
                subject_url, 
                limit=100, 
                min_year=year, 
                max_year=year, 
                existing_urls=[], 
                exam_type=exam_type,
                question_type=question_type
            )
            
            # Robust filtering
            year_questions = []
            for q in year_data:
                if q['year'] == year or q['year'] is None:
                    q['year'] = year
                    q['question_type'] = question_type
                    year_questions.append(q)
            
            if year_questions:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(year_questions, f, indent=2)
                print(f"  Year {year}: Saved {len(year_questions)} questions to local cache.")
            else:
                # Check if we were blocked before saving 0
                if getattr(scraper, 'was_blocked', False):
                    print(f"  Year {year}: Scrape failed due to potential block. Not caching empty result.")
                else:
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump([], f)
                    print(f"  Year {year}: No questions found on MySchool.")

        # Track how many from this year are actually new
        new_in_year = 0
        for q in year_questions:
            found_any_matching = True
            q['subject'] = subject_name
            q['question_type'] = question_type
            
            is_new = True
            if q['source_url'] and q['source_url'] in existing_urls:
                is_new = False
            
            if is_new:
                if q['source_url'] not in [sq['source_url'] for sq in all_questions if sq.get('source_url')]:
                    all_questions.append(q)
                    new_in_year += 1
        
        if year_questions and new_in_year > 0:
            print(f"  -> Added {new_in_year} new questions to upload queue.")

    if not all_questions:
        print("\nNo new questions found for upload. All questions from these years are already on your Render server.")
        print("However, they have been saved to your local 'data/' folder for offline access.")
        return

    print(f"\nTotal new questions ready for upload: {len(all_questions)}")
    
    # 5. Push to Remote
    confirm = input(f"Do you want to upload these {len(all_questions)} questions to {REMOTE_URL}? (y/n): ")
    if confirm.lower() != 'y':
        print("Upload cancelled.")
        return

    print("Uploading to remote server...")
    try:
        # Post to the new bulk endpoint
        sync_resp = requests.post(
            f"{REMOTE_URL}/questions/bulk",
            json=all_questions,
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
