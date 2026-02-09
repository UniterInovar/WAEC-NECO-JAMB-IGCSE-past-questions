import requests
from bs4 import BeautifulSoup

def inspect_subjects():
    url = "https://myschool.ng/classroom"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Look for subject links
        links = soup.select('a[href*="/classroom/"]')
        found = []
        for l in links:
            href = l.get('href', '')
            text = l.text.strip()
            # Most subject links are simply https://myschool.ng/classroom/biology
            if text and '/classroom/' in href and not any(x in href for x in ['topic', 'exam', 'video', 'news', 'jamb', 'novel', 'brochure', 'syllabus']):
                found.append({'name': text, 'url': href})
        
        print(f"Total links found: {len(found)}")
        for f in found[:50]:
            print(f"{f['name']} | {f['url']}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_subjects()
