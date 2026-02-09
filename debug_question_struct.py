import requests
from bs4 import BeautifulSoup
import re

def debug_question(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # The h3 is truncated. Let's find the tag that has the full text.
    body_tag = soup.find('h3')
    if body_tag:
        prefix = body_tag.text.strip().replace('...', '')
        print(f"\nSearching for full text starting with: {prefix[:50]}...")
        
        # Look for the question content. 
        # Often it is in a div or p near the h3.
        # Let's search for all tags and check their text.
        for tag in soup.find_all(['div', 'p']):
            content = tag.get_text(strip=True)
            if content.startswith(prefix) and len(content) > len(body_tag.text.strip()):
                print(f"Found potential full body in <{tag.name}>:")
                print(content[:500])
                break
    
    # Let's also search for scientific-looking patterns in raw text
    text = soup.get_text()
    matches = re.findall(r'[A-Z][a-z]?\(?\d\)?', text) # CO(2), H2O, etc.
    if matches:
        print(f"\nPotential scientific patterns found: {list(set(matches))[:10]}")

    # Check for LaTeX/Scientific notations
    print(f"\n--- Raw HTML snippet around scientific notation ---")
    print(soup.prettify()[:2000]) # Print first bit to see structure

if __name__ == "__main__":
    # Test a chemistry question likely to have formulas
    test_url = "https://myschool.ng/classroom/chemistry/7" 
    debug_question(test_url)
