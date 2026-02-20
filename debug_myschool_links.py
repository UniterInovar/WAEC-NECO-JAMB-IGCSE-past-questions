import requests
from bs4 import BeautifulSoup
import re
import time

def debug_myschool():
    url = "https://myschool.ng/classroom/chemistry?exam_type=waec&exam_year=2023&type=objective"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    }
    
    print(f"Fetching {url}...")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Body snippet: {response.text[:500]}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        print(f"Title: {soup.title.string if soup.title else 'No Title'}")
        
        # Check for block
        if "captcha" in response.text.lower() or "bot detection" in response.text.lower():
            print("BLOCKED BY CAPTCHA")
            return

        if "Chemistry" not in response.text:
            print("WARNING: 'Chemistry' not found in page text!")
        
        # Search for script tags
        scripts = soup.find_all('script')
        print(f"\nNumber of script tags: {len(scripts)}")
        for i, s in enumerate(scripts):
            content = s.string if s.string else ""
            if len(content) > 1000:
                print(f"Large script tag {i} (len={len(content)}). Snippet: {content[:200]}...")
        
        # Search for any string that looks like "Question" or "1."
        if "1." in response.text:
            print("Found '1.' in text. Snippet of surrounding:")
            idx = response.text.find("1.")
            print(response.text[max(0, idx-100):idx+500])
        else:
            print("'1.' not found in text.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_myschool()
