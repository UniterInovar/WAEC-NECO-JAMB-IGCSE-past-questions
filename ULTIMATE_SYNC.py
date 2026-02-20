import requests
from bs4 import BeautifulSoup
import time
import random
import os
import json
import sys

# Add current directory to path
sys.path.append(os.getcwd())
from scrapers.myschool_scraper import MySchoolScraper

def ultimate_sync():
    DEFAULT_URL = "https://waec-neco-jamb-igcse-past-questions.onrender.com"
    
    print("\n" + "="*40)
    print("      Past Questions Sync (ULTIMATE)     ")
    print("="*40)
    
    # 1. Verify environment
    if not os.path.exists("scrapers") or not os.path.exists("backend"):
        print("\nERROR: Please run this script from the project root folder:")
        print("c:\\Users\\USER\\OneDrive\\Desktop\\Resource materials")
        return

    # 2. Server Connection
    server_url = input(f"\nRender Server URL [{DEFAULT_URL}]: ").strip() or DEFAULT_URL
    if server_url.endswith('/'): server_url = server_url[:-1]
    
    print(f"Connecting to {server_url}...")
    try:
        r = requests.get(f"{server_url}/api/health", timeout=15)
        if r.status_code == 200:
            print("Online!")
        else:
            print(f"CONNECTED BUT ERROR: Status {r.status_code}")
            print(f"Message: {r.text}")
            return
    except Exception as e:
        print(f"\nCOULD NOT CONNECT: {e}")
        print("\nNOTE: Because you used the Blueprint, your URL might have changed.")
        print("Check your Render Dashboard for a service named 'past-questions-api'.")
        print("It will look like: https://past-questions-api-xxxx.onrender.com")
        return

    # 3. Choose Action
    print("\nSelect Source:")
    print("1. MySchool (Scrape Website - Stealth Mode)")
    print("2. ALOC (Reliable API - Requires Access Token)")
    choice = input("Choice [1]: ").strip() or "1"
    
    if choice == "2":
        print("\n--- ALOC API Sync ---")
        print("Note: ALOC mostly provides Objective questions for JAMB/WAEC/NECO.")
        subject = input("Subject (e.g. Chemistry): ").strip().lower()
        count = input("Count [50]: ").strip() or "50"
        
        token = input("\nEnter your ALOC Access Token (Get one at aloc.ng): ").strip()
        if not token:
            print("ERROR: ALOC requires an Access Token for bulk syncing. Please get one at https://aloc.ng")
            return

        print(f"\nFetching {count} {subject} questions from ALOC API...")
        aloc_url = f"https://questions.aloc.com.ng/api/v2/m?subject={subject}&count={count}"
        headers = {"AccessToken": token}
        
        try:
            r = requests.get(aloc_url, headers=headers, timeout=30)
            if r.status_code != 200:
                print(f"ALOC API Error {r.status_code}: {r.text}")
                return
            
            data = r.json().get('data', [])
            if not data:
                print("No questions returned from ALOC for this subject.")
                return
                
            print(f"Fetched {len(data)} questions. Formatting...")
            formatted = []
            for q in data:
                options = [q['option']['a'], q['option']['b'], q['option']['c'], q['option']['d']]
                if q['option'].get('e'): options.append(q['option']['e'])
                
                formatted.append({
                    "body": q['question'],
                    "options": options,
                    "answer": q['answer'].upper() if q['answer'] else 'A',
                    "explanation": q.get('solution'),
                    "subject": subject,
                    "year": int(q['examyear']) if str(q.get('examyear')).isdigit() else None,
                    "exam_type": q.get('examtype', 'jamb').lower(),
                    "question_type": "objective",
                    "topic": "General",
                    "source_url": f"aloc-{q['id']}"
                })
            
            print(f"Sending to your Render server at {server_url}...")
            res = requests.post(f"{server_url}/questions/bulk", json=formatted)
            print(f"Server Response: {res.json().get('message', res.text)}")
        except Exception as e:
            print(f"ALOC Sync Failed: {e}")
        return

    # 4. Scrape Mode
    subject = input("\nSubject (e.g. Chemistry): ").strip()
    exam = input("Exam Type (jamb/waec/neco): ").strip().lower()
    q_type = input("Type (objective/theory) [objective]: ").strip().lower() or "objective"
    limit = int(input("Limit [50]: ").strip() or "50")

    scraper = MySchoolScraper()
    
    # Enhanced logic: Skip years already on remote to save requests
    print("\nChecking remote status...")
    remote_resp = requests.get(f"{server_url}/questions?subject={subject}&question_type={q_type}")
    remote_urls = []
    if remote_resp.status_code == 200:
        remote_urls = [q['source_url'] for q in remote_resp.json() if q.get('source_url')]
        print(f"Already have {len(remote_urls)} questions on server.")

    all_found = []
    current_year = 2025 # Fixed year focus
    
    for year in range(current_year, 2000, -1):
        if len(all_found) >= limit: break
        
        # Check local cache first
        cache_dir = f"data/{subject.lower().replace(' ','_')}/{exam}/{year}/{q_type}"
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = f"{cache_dir}/questions.json"
        
        year_qs = []
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                year_qs = json.load(f)
        
        if not year_qs:
            print(f"-- Year {year}: Scraping (Wait 3-7s) --")
            sub_url = f"https://myschool.ng/classroom/{subject.lower().replace(' ','-')}"
            year_qs = scraper.scrape_questions(sub_url, limit=50, min_year=year, max_year=year, exam_type=exam, question_type=q_type)
            
            if year_qs:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(year_qs, f, indent=2)
            elif getattr(scraper, 'was_blocked', False):
                print(f"!! BLOCKED BY MYSCHOOL for year {year} !!")
                print("Try again in 5 minutes or use ALOC (Choice 2).")
                break
        
        for q in year_qs:
            if q['source_url'] not in remote_urls:
                q['subject'] = subject
                all_found.append(q)
                
        if len(all_found) >= limit: break

    if not all_found:
        print("\nNo new questions found to upload.")
    else:
        print(f"\nFound {len(all_found)} NEW questions!")
        confirm = input("Upload now? (y/n): ").strip().lower()
        if confirm == 'y':
            print("Uploading...")
            res = requests.post(f"{server_url}/questions/bulk", json=all_found)
            print(f"Server: {res.json().get('message', res.text)}")

if __name__ == "__main__":
    try:
        ultimate_sync()
    except KeyboardInterrupt:
        print("\nStopped.")
    except Exception as e:
        print(f"\nError: {e}")
    input("\nPress Enter to exit...")
