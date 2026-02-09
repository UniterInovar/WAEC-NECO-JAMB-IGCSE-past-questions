import fitz  # PyMuPDF
import re

class IGCSEParser:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path

    def extract_text(self):
        doc = fitz.open(self.pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        return full_text

    def parse_questions(self, text):
        # Very basic regex-based parser for IGCSE papers
        # Usually questions are numbered: 1, 2, 3...
        # This is a complex task and usually needs custom logic per exam board/year
        questions = []
        pattern = re.compile(r'(\d+)\s+(.*?)(?=\n\s*\d+\s+|$)', re.DOTALL)
        matches = pattern.findall(text)
        
        for match in matches:
            questions.append({
                'number': match[0],
                'body': match[1].strip()
            })
        return questions
