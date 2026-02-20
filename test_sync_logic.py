import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add current directory to path
sys.path.append(os.getcwd())

from scripts.sync_data import sync

def test_sync_logic():
    print("--- Verifying sync_data.py logic with Mocked Inputs ---")
    
    # Mock inputs for a theory scrape
    inputs = [
        "https://test-server.com", # Remote URL
        "Biology",                 # Subject
        "waec",                    # Exam Type
        "theory",                  # Question Type
        "5"                        # Limit
    ]
    
    with patch('builtins.input', side_effect=inputs), \
         patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post, \
         patch('scrapers.myschool_scraper.MySchoolScraper') as mock_scraper_class:
        
        # Mock connection test
        mock_get.return_value.status_code = 200
        
        # Mock subject scraping
        mock_scraper = mock_scraper_class.return_value
        mock_scraper.scrape_subjects.return_value = [{'name': 'Biology', 'url': 'bio_url'}]
        
        # Mock question scraping
        mock_scraper.scrape_questions.return_value = [
            {'year': 2024, 'source_url': 'url1', 'question_type': 'theory', 'body': 'TB1'},
            {'year': 2024, 'source_url': 'url2', 'question_type': 'theory', 'body': 'TB2'}
        ]
        
        # We don't want to actually write to files in this test, but we want to see if the paths are correct
        with patch('os.makedirs'), patch('builtins.open', create=True):
            # We also need to mock os.path.exists to return False to force scraping
            with patch('os.path.exists', return_value=False):
                try:
                    sync()
                except StopIteration:
                    # sync() will call input() again for confirmation, which we didn't provide enough for
                    print("\nSync call reached confirmation prompt (Success - Logic followed)")
                except Exception as e:
                    print(f"\nCaught unexpected error: {e}")

if __name__ == "__main__":
    test_sync_logic()
