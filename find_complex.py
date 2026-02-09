import requests
from bs4 import BeautifulSoup

def find_complex_questions():
    url = "https://myschool.ng/classroom/chemistry"
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    links = soup.find_all('a')
    for l in links:
        if 'View Answer & Discuss' in l.get_text():
            # Get the question teaser text
            # Usually it's in a sibling or parent
            teaser = l.find_previous('div').get_text() if l.find_previous('div') else ""
            if '(' in teaser or ')' in teaser or any(char.isdigit() for char in teaser):
                print(f"Complex question URL: {l['href']}")
                print(f"Teaser: {teaser.strip()[:100]}...")

if __name__ == "__main__":
    find_complex_questions()
