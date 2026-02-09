import requests
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod

class BaseScraper(ABC):
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_soup(self, url):
        response = self.session.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')

    @abstractmethod
    def scrape_subjects(self):
        pass

    @abstractmethod
    def scrape_questions(self, subject_url):
        pass
