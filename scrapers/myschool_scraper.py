import requests
from bs4 import BeautifulSoup
import re
import time
from concurrent.futures import ThreadPoolExecutor
import copy

class MySchoolScraper:
    def __init__(self):
        self.base_url = "https://myschool.ng"
        self.session = requests.Session()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1'
        ]
        self.update_headers()

    def update_headers(self):
        import random
        self.headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://myschool.ng/classroom'
        }

    def get_soup(self, url):
        import random
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # Randomized delay
                time.sleep(random.uniform(2.0, 5.0))
                self.update_headers()
                
                response = self.session.get(url, headers=self.headers, timeout=15)
                self.last_status = response.status_code
                
                if response.status_code == 403:
                    print(f"WARNING: 403 Forbidden at {url}. Attempt {attempt+1}/{max_retries}")
                    self.was_blocked = True
                    if attempt < max_retries - 1:
                        time.sleep(10) # Heavy delay on fail
                        continue
                
                # Check for common bot detection patterns in HTML
                bot_keywords = ["captcha", "bot detection", "challenge-platform", "one more step", "please verify you are a human"]
                text_lower = response.text.lower()
                if any(k in text_lower for k in bot_keywords):
                    print(f"WARNING: Bot detection keywords found at {url}")
                    self.was_blocked = True
                else:
                    self.was_blocked = False
                    
                return BeautifulSoup(response.text, 'html.parser')
            except Exception as e:
                print(f"Error fetching {url}: {e}")
                self.was_blocked = False
                if attempt < max_retries - 1:
                    continue
                return None
        return None

    def scrape_subjects(self):
        import json
        import os
        
        cache_file = "subjects.json"
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error reading cache: {e}")

        url = f"{self.base_url}/classroom"
        soup = self.get_soup(url)
        subjects = []
        if soup:
            links = soup.select('a[href*="/classroom/"]')
            seen_urls = set()
            for link in links:
                name = link.text.strip()
                href = link['href']
                if not href.startswith('http'):
                    href = self.base_url + href
                
                # Extract the part after /classroom/
                path = href.replace(self.base_url + "/classroom/", "")
                
                # Filter for subject landing pages (shallow path, no weird keywords)
                if path and '/' not in path and name:
                    # Skip meta-links and noise
                    exclude = ['video', 'news', 'jamb', 'waec', 'neco', 'novel', 'brochure', 'syllabus', 'questions', 'performance', 'exam', 'member', 'practice', 'topics']
                    if not any(x in path.lower() for x in exclude) and "Questions" not in name and "Exam" not in name:
                        if href not in seen_urls:
                            subjects.append({'name': name, 'url': href})
                            seen_urls.add(href)
        
        if subjects:
            try:
                with open(cache_file, 'w') as f:
                    json.dump(subjects, f)
            except Exception as e:
                print(f"Error writing cache: {e}")
                
        return subjects

    def extract_details_from_soup(self, soup, detail_url):
        if not soup:
            return None, None, None, None, None, None

        # Extract answer
        answer_tag = soup.find(string=re.compile(r'Correct Answer: Option'))
        answer = ""
        if answer_tag:
            answer = answer_tag.split('Option')[-1].strip()

        # Extract explanation
        explanation_header = soup.find('h5', string=re.compile(r'Explanation', re.I))
        explanation = ""
        if explanation_header:
            # The explanation is often in a div following the h5
            explanation_container = explanation_header.find_next(['div', 'p'])
            if explanation_container:
                explanation = self.clean_scientific_text(explanation_container, subject=detail_url)
            else:
                next_node = explanation_header.next_sibling
                if next_node:
                    explanation = self.clean_scientific_text(next_node, subject=detail_url)

        # Extract exam type, year and topic
        topic = "General"
        tags = soup.select('a[href*="/classroom/topic/"]')
        if tags:
            topic = tags[0].text.strip()

        # Extract exam type and year
        exam_link = soup.select_one('a[href*="exam_type="]')
        exam_type = "jamb"
        year = None
        if exam_link:
            href = exam_link['href']
            type_match = re.search(r'exam_type=([^&]+)', href)
            year_match = re.search(r'exam_year=(\d+)', href)
            if type_match:
                exam_type = type_match.group(1)
            if year_match:
                year = int(year_match.group(1))

        return answer, explanation, exam_type, year, topic, detail_url

    def clean_scientific_text(self, node, subject=""):
        """Processes a BeautifulSoup node to preserve images and clean scientific text."""
        if not node:
            return ""
        
        # Determine if we should be aggressive with chemistry formatting
        subject_lower = subject.lower() if subject else ""
        is_english = "english" in subject_lower
        is_science = any(s in subject_lower for s in ["chem", "bio", "phys", "science"])
        if isinstance(node, str):
            text = node
        else:
            # For BeautifulSoup nodes, handle images and then get content
            for img in node.find_all('img'):
                if 'src' in img.attrs:
                    src = img['src']
                    if src.startswith('/'):
                        img['src'] = self.base_url + src
                    # Ensure images have some basic styling if needed
                    img['style'] = "max-width: 100%; height: auto; display: block; margin: 10px 0;"
            
            # Use decode_contents to keep tags like <sub>, <sup>, and <img>
            # We want to keep <br>, <u>, <b>, <i> etc.
            text = node.decode_contents()

        if not text:
            return ""
            
        # Fix encoding issues (common in MySchool.ng)
        text = text.replace('\xa0', ' ').replace('&nbsp;', ' ')
        
        # Replace common mis-encoded characters like U+FFFD (replacement character)
        text = text.replace('\ufffd', "'")

        # Remove LaTeX delimiters which often cause (CO2) instead of CO2
        text = text.replace(r'\(', '').replace(r'\)', '').replace(r'\[', '').replace(r'\]', '')

        # Handle LaTeX style subscripts/superscripts (mostly for science)
        if is_science or not is_english:
            text = re.sub(r'\\?_\{([^}]+)\}', r'<sub>\1</sub>', text)
            text = re.sub(r'_\{([^}]+)\}', r'<sub>\1</sub>', text)
            text = re.sub(r'_(\d)', r'<sub>\1</sub>', text)
            text = re.sub(r'\\?\^\{([^}]+)\}', r'<sup>\1</sup>', text)
            text = re.sub(r'\^\{([^}]+)\}', r'<sup>\1</sup>', text)
            text = re.sub(r'\^(\d)', r'<sup>\1</sup>', text)
            
            # Chemical symbols and arrows
            text = text.replace(r'\to', '→').replace(r'\uparrow', '↑').replace(r'\downarrow', '↓')
            text = text.replace(r'\lambda', 'λ').replace(r'\theta', 'θ')
            text = text.replace(r'\times', '×').replace(r'\div', '÷')

            # Handle plain text chemical formulas like CO2, H2O (capital letter + digit)
            def chem_sub(match):
                return f"{match.group(1)}<sub>{match.group(2)}</sub>"
            
            # Pattern to find chemical formulas: Capital letter (+ lowercase) followed by digits
            # Refining to avoid common English words/patterns
            # Only apply if it looks like a formula (e.g., ends in digit or followed by science context)
            text = re.sub(r'([A-Z][a-z]?)([2-9])(?![a-zA-Z])', chem_sub, text)
            
            # Electronic configuration (spdf notation)
            text = re.sub(r'\b([1-7][spdf])(\d{1,2})\b', r'\1<sup>\2</sup>', text)

            # Handle LaTeX fractions \frac{num}{den}
            text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'<sup>\1</sup>&frasl;<sub>\2</sub>', text)

        return text.strip()

    def process_detail_page(self, detail_url, force_type=None):
        """Worker function for multi-threaded scraping."""
        detail_soup = self.get_soup(detail_url)
        if not detail_soup:
            return None
        
        answer, explanation, exam_type, year, topic, source_url = self.extract_details_from_soup(detail_soup, detail_url)
        
        # Look for the full body in question-desc
        body_container = detail_soup.find('div', class_='question-desc')
        if body_container:
            # Clone and remove badges
            body_copy = copy.copy(body_container)
            for badge in body_copy.find_all('a'):
                badge.decompose()
            
            # Specific cleanup for video links/text often found in myschool
            for vid in body_copy.find_all('a', href=True):
                if 'explanation_video' in vid['href'] or 'video' in vid.text.lower():
                    vid.decompose()
            
            for string in body_copy.find_all(string=True):
                s_lower = string.lower()
                if ("explanation_video" in s_lower or "[below]" in s_lower or "view answer" in s_lower) and len(string) < 60:
                    string.replace_with("")

            body = self.clean_scientific_text(body_copy, subject=detail_url) 
        else:
            # Fallback to h3 if question-desc not found
            body_tag = detail_soup.find('h3')
            if not body_tag:
                return None
            body = self.clean_scientific_text(body_tag, subject=detail_url)
            body = re.sub(r'\.{3,}$', '', body)

        options = []
        valid_items = []
        
        # Try to find options in ul.list-unstyled first
        options_container = detail_soup.find('ul', class_='list-unstyled')
        if options_container:
            valid_items = options_container.find_all('li')
        else:
            found_body = False
            for item in detail_soup.find_all(['h3', 'li', 'h4', 'h5']):
                if item.name == 'h3' and 'page-title' in item.get('class', []):
                    found_body = True
                    continue
                if not found_body:
                    continue
                if item.name in ['h4', 'h5'] and ('Contribution' in item.text or 'Quick Question' in item.text or 'Sign In' in item.text):
                    break
                if item.name == 'li':
                    valid_items.append(item)

        letters = ['A', 'B', 'C', 'D', 'E']
        for letter in letters:
            found = False
            for item in valid_items:
                text = item.get_text(strip=True)
                if re.match(rf'^{letter}[.\s\)]?\s*.+', text, re.IGNORECASE):
                    item_copy = copy.copy(item)
                    strong = item_copy.find('strong')
                    if strong and re.match(rf'^{letter}[.\s\)]?\s*$', strong.get_text(strip=True), re.IGNORECASE):
                        strong.decompose()
                    
                    cleaned_html = self.clean_scientific_text(item_copy, subject=detail_url)
                    cleaned_html = re.sub(rf'^{letter}([.\s\)])\s*', '', cleaned_html, flags=re.IGNORECASE)
                    cleaned_html = re.sub(r'^[\s\.]+', '', cleaned_html).strip()
                    
                    options.append(cleaned_html)
                    found = True
                    break
            if not found:
                if not (year and year >= 2000 and letter == 'E'):
                    options.append("")

        # Determine if it's objective or theory
        non_empty_options = [o for o in options if o.strip()]
        if force_type:
            q_type = force_type
        else:
            q_type = 'objective' if len(non_empty_options) >= 2 else 'theory'

        return {
            'body': body,
            'options': options if q_type == 'objective' else [],
            'answer': answer,
            'explanation': explanation,
            'exam_type': exam_type,
            'year': year,
            'question_type': q_type,
            'topic': topic,
            'source_url': source_url
        }

    def scrape_questions(self, subject_url, limit=50, min_year=2000, max_year=None, existing_urls=None, exam_type=None, question_type=None):
        questions = []
        import datetime
        current_year = max_year if max_year else datetime.datetime.now().year
        existing_urls = set(existing_urls or [])
        
        # Determine exam types to scrape
        target_types = [exam_type] if exam_type else ['jamb', 'waec', 'neco']
        
        # Determine question types to scrape
        # If user specifies 'theory', we should also check 'practical' as they are often separate on MySchool
        q_types_to_try = [question_type] if question_type else ['objective', 'theory', 'practical']
        if question_type == 'theory':
            q_types_to_try = ['theory', 'practical']

        for etype in target_types:
            for qtype in q_types_to_try:
                if len(questions) >= limit:
                    break
                    
                # Iterate backwards from current_year to min_year
                for year in range(current_year, min_year - 1, -1):
                    if len(questions) >= limit:
                        break
                        
                    page = 1
                    while len(questions) < limit:
                        # Construct URL with exam_type, exam_year, and type (objective/theory/practical)
                        url = f"{subject_url}?page={page}&exam_type={etype}&exam_year={year}&type={qtype}"
                        print(f"Scraping: {etype} {year} ({qtype}) Page {page}")
                        
                        soup = self.get_soup(url)
                        if not soup:
                            break

                        # Find all links that contain "View Answer" or "Discuss"
                        all_links = soup.find_all('a', href=re.compile(r'/classroom/questions/'))
                        detail_links = []
                        for l in all_links:
                            link_text = l.get_text().strip()
                            if "View Answer" in link_text or "Discuss" in link_text or "Question Detail" in link_text:
                                detail_links.append(l)

                        if not detail_links:
                            # If no detail links but many other links exist, maybe the text changed
                            # Look specifically for links that look like question links
                            if len(all_links) > 10:
                                print(f"DEBUG: Found {len(all_links)} links but none matched 'View Answer'. Trying fallback...")
                            break

                        urls_to_fetch = []
                        for link in detail_links:
                            detail_url = link.get('href')
                            if not detail_url:
                                continue
                            if not detail_url.startswith('http'):
                                detail_url = self.base_url + detail_url
                                
                            if detail_url not in existing_urls:
                                urls_to_fetch.append(detail_url)

                        if not urls_to_fetch:
                            if page > 5: break
                            page += 1
                            continue

                        # Process in parallel, passing the current qtype as the forced type
                        # because 'practical' should be saved as 'theory' but fetched via 'practical' param
                        forced_type = 'theory' if qtype in ['theory', 'practical'] else 'objective'
                        
                        with ThreadPoolExecutor(max_workers=5) as executor:
                            results = list(executor.map(lambda u: self.process_detail_page(u, force_type=forced_type), urls_to_fetch))

                        for res in results:
                            if res:
                                res_year = res['year']
                                res_type = (res['exam_type'].lower() if res['exam_type'] else '')
                                target_type = etype.lower()
                                
                                year_match = (res_year == year or res_year is None)
                                type_match = (res_type == target_type or res_type == '')
                                
                                if year_match and type_match:
                                    if len(questions) < limit:
                                        if res['source_url'] not in [q['source_url'] for q in questions]:
                                            questions.append(res)
                        
                        matching_in_this_batch = [r for r in results if r and (r['year'] == year or r['year'] is None) and (not r['exam_type'] or r['exam_type'].lower() == target_type)]
                        
                        if results and not matching_in_this_batch:
                            print(f"No matching questions found for {etype} {year} {qtype} on Page {page}. Skipping year for this type.")
                            break
                        
                        pagination = soup.find('a', href=re.compile(rf'page={page + 1}'))
                        if not pagination:
                            break
                        page += 1
                    
        return questions
