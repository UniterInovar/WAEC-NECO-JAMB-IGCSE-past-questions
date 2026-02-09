import requests
from bs4 import BeautifulSoup

def debug_subjects():
    base_url = "https://myschool.ng"
    url = f"{base_url}/classroom"
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    links = soup.select('a[href*="/classroom/"]')
    
    seen_urls = set()
    subjects = []
    
    for link in links:
        name = link.text.strip()
        href = link['href']
        if not href.startswith('http'):
            href = base_url + href
            
        path = href.replace(base_url + "/classroom/", "")
        
        if path and '/' not in path and name:
            exclude = ['video', 'news', 'jamb', 'waec', 'neco', 'novel', 'brochure', 'syllabus', 'questions', 'performance', 'exam', 'member', 'practice', 'topics']
            is_excluded = any(x in path.lower() for x in exclude) or "Questions" in name or "Exam" in name
            
            if not is_excluded:
                if href not in seen_urls:
                    subjects.append({'name': name, 'url': href})
                    seen_urls.add(href)
                
    print(f"Final subjects count: {len(subjects)}")
    for s in subjects:
        print(f"{s['name']}")

if __name__ == "__main__":
    debug_subjects()
