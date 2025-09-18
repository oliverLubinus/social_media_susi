"""
test_susi_image_internal_workflow.py: Unit tests for Susi's internal workflow modules (OneDrive, metadata extraction, post generation, email).

Features:
    - Tests OneDrive download, metadata extraction, post generation, and email logic in isolation.
    - Mocks all external dependencies to ensure fast, isolated, and safe tests.

Developer hints:
    - All network, file I/O, and email calls are mocked; no real API calls or file writes are made.
    - Adjust mock return values and side effects to simulate new edge cases or errors.
    - Use assert_called_once, assertIn, and MagicMock to verify correct logic.

Error/warning message hints:
    - If you see real network or file I/O, check that all relevant functions are patched/mocked.
    - If a test fails, check assertion logic and mock return values.
    - For new workflow logic, update or add tests to match expected behavior.
"""
import unittest
from unittest.mock import patch, MagicMock
from susi.onedrive_monitor import download_onedrive_image
from susi.metadata import extract_metadata
import susi.post_generator
import susi.email_utils
import os

class TestOneDriveDownload(unittest.TestCase):
    """
    Unit tests for OneDrive image download logic in Susi.

    Mocks requests.get and download_onedrive_image to simulate download success.
    """
    @patch('requests.get')
    @patch('susi.onedrive_monitor.download_onedrive_image')
    def test_download_onedrive_image(self, mock_download, mock_requests_get):
        """
        Test: download_onedrive_image returns correct local path on success.
        """
        mock_download.return_value = os.path.normpath('downloads/test.jpg')
        mock_requests_get.return_value = MagicMock(status_code=200, content=b'fake')
        # Provide required key to avoid KeyError
        item = {'id': '1', 'name': 'test.jpg', '@microsoft.graph.downloadUrl': 'https://dummy_url'}
        result = download_onedrive_image(item)
        self.assertEqual(result, os.path.normpath('downloads/test.jpg'))

class TestMetadataExtraction(unittest.TestCase):
    """
    Unit tests for metadata extraction logic in Susi.

    Mocks extract_metadata and open to simulate metadata extraction.
    """
    @patch('susi.metadata.extract_metadata')
    @patch('builtins.open', new_callable=MagicMock)
    def test_extract_metadata(self, mock_open, mock_extract):
        """
        Test: extract_metadata returns dict with 'title' and 'comment'.
        """
        mock_extract.return_value = {'title': 'Test', 'comment': 'A comment'}
        result = extract_metadata('downloads/test.jpg')
        self.assertIn('title', result)
        self.assertIn('comment', result)

class TestPostGeneration(unittest.TestCase):
    """
    Unit tests for post generation and email logic in Susi.

    Mocks generate_post_text, send_error_email, and send_gmail to simulate logic.
    """
    @patch('susi.post_generator.generate_post_text', return_value='Test caption')
    def test_generate_post_text(self, mock_generate):
        """
        Test: generate_post_text returns expected caption.
        """
        result = susi.post_generator.generate_post_text({'title': 'Test', 'comment': 'A comment'}, '{title}\n{comment}')
        self.assertEqual(result, 'Test caption')

    @patch('susi.email_utils.send_error_email', return_value=None)
    def test_send_error_email(self, mock_send_error):
        """
        Test: send_error_email is called with correct arguments.
        """
        susi.email_utils.send_error_email('subject', 'body', {'email': {'username': 'dummy', 'recipient': 'dummy'}})
        mock_send_error.assert_called_once()

    @patch('susi.email_utils.send_gmail', return_value=None)
    def test_send_gmail(self, mock_send):
        """
        Test: send_gmail is called with correct arguments.
        """
        susi.email_utils.send_gmail('subject', 'body', {'email': {'username': 'dummy', 'recipient': 'dummy'}})
        mock_send.assert_called_once()

if __name__ == '__main__':
    unittest.main()
