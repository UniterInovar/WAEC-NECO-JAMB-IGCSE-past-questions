import requests
import os
from dotenv import load_dotenv

load_dotenv()

class ALOCClient:
    def __init__(self):
        self.base_url = "https://questions.aloc.com.ng/api/v2"
        self.token = os.getenv("ALOC_TOKEN")

    def get_question(self, subject, year=None, type=None):
        params = {"subject": subject}
        if year:
            params["year"] = year
        if type:
            params["type"] = type
        
        headers = {}
        if self.token:
            headers["AccessToken"] = self.token

        response = requests.get(f"{self.base_url}/q", params=params, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None

    def get_multiple_questions(self, subject, count=10):
        params = {"subject": subject, "count": count}
        headers = {}
        if self.token:
            headers["AccessToken"] = self.token

        response = requests.get(f"{self.base_url}/m", params=params, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
