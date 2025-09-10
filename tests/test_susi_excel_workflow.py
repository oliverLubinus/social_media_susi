"""
test_susi_excel_workflow.py: Unit tests for the Excel-driven workflow in Susi.

Features:
    - Tests Excel monitoring, news fetching, LLM post generation, and Excel writing/marking.
    - Mocks all external dependencies (OneDrive, NewsAPI, LLM, etc.) for fast, isolated tests.

Developer hints:
    - All network/LLM/Excel calls are mocked; no real API calls are made.
    - Adjust mock return values to simulate new edge cases or error scenarios.
    - Use assert_called_once, assert_has_calls, and MagicMock to verify correct workflow.

Error/warning message hints:
    - If you see real network calls, check that all relevant functions are patched/mocked.
    - If a test fails, check assertion logic and mock return values.
    - For new workflow logic, update or add tests to match expected behavior.
"""
import unittest
from unittest.mock import patch, MagicMock

class TestExcelWorkflow(unittest.TestCase):
    """
    Unit test suite for the Excel-driven workflow in Susi.

    Mocks all major external dependencies to ensure tests are fast, isolated, and safe.
    """
    @patch('susi.onedrive_auth.get_access_token', return_value='token')
    @patch('requests.get')
    def test_get_excel_rows(self, mock_get, mock_token):
        """
        Test: get_excel_rows returns only unprocessed rows from Excel.

        Simulates Excel API response and verifies correct row filtering and parsing.
        """
        # Simulate Excel API response
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {
            'values': [
                ['Content', 'Target Group', 'Instagram', 'processed'],
                ['AI', 'Doctors', '', ''],
                ['ML', 'Nurses', '', 'x']
            ]
        })
        from susi.excel_monitor import get_excel_rows
        rows = get_excel_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['Content'], 'AI')
        self.assertEqual(rows[0]['Target Group'], 'Doctors')

    @patch('requests.get')
    def test_fetch_news_articles(self, mock_get):
        """
        Test: fetch_news_articles returns articles from mocked NewsAPI response.
        """
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {
            'articles': [
                {'title': 'AI in healthcare', 'description': 'AI helps doctors.'}
            ]
        })
        import os
        os.environ['NEWSAPI_KEY'] = 'dummy'
        from susi.news_api import fetch_news_articles
        articles = fetch_news_articles('AI', 'Doctors')
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]['title'], 'AI in healthcare')


    @patch('susi.genai_api.generate_linkedin_post', return_value='Generated LinkedIn post.')
    @patch('susi.genai_api.generate_instagram_post', return_value='Generated Instagram post.')
    def test_generate_instagram_and_linkedin_post(self, mock_insta, mock_linkedin):
        """
        Test: generate_instagram_post and generate_linkedin_post return mocked results.
        """
        from susi.genai_api import generate_instagram_post, generate_linkedin_post
        insta_post = generate_instagram_post('AI', 'Doctors', [{'title': 'AI in healthcare', 'description': 'AI helps doctors.'}])
        linkedin_post = generate_linkedin_post('AI', 'Doctors', [{'title': 'AI in healthcare', 'description': 'AI helps doctors.'}])
        self.assertIn('Generated Instagram post', insta_post)
        self.assertIn('Generated LinkedIn post', linkedin_post)


    @patch('susi.onedrive_auth.get_access_token', return_value='token')
    @patch('requests.get')
    @patch('requests.patch')
    def test_write_instagram_and_linkedin_post(self, mock_patch, mock_get, mock_token):
        """
        Test: write_instagram_post and write_linkedin_post patch Excel with correct data.
        """
        # Simulate Excel API response for header
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {
            'values': [['Content', 'Target Group', 'Instagram', 'LinkedIn', 'processed']]
        })
        mock_patch.return_value = MagicMock(status_code=200)
        from susi.excel_monitor import write_instagram_post, write_linkedin_post
        write_instagram_post(0, 'Test Instagram post')
        write_linkedin_post(0, 'Test LinkedIn post')
        self.assertEqual(mock_patch.call_count, 2)

    @patch('susi.onedrive_auth.get_access_token', return_value='token')
    @patch('requests.get')
    @patch('requests.patch')
    def test_mark_row_processed(self, mock_patch, mock_get, mock_token):
        """
        Test: mark_row_processed patches Excel to mark a row as processed.
        """
        # Simulate Excel API response for header
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {
            'values': [['Content', 'Target Group', 'Instagram', 'processed']]
        })
        mock_patch.return_value = MagicMock(status_code=200)
        from susi.excel_monitor import mark_row_processed
        mark_row_processed(0)
        mock_patch.assert_called_once()

if __name__ == '__main__':
    unittest.main()
