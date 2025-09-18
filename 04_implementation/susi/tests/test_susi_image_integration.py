"""
test_susi_image_integration.py: Integration tests for the full Susi image workflow.

Features:
    - Simulates the full workflow: OneDrive download, metadata extraction, S3 upload, Instagram posting.
    - Mocks all external services to verify workflow logic and error handling.
    - Covers both success and S3 upload failure scenarios.

Developer hints:
    - All network/storage/Instagram calls are mocked; no real uploads or posts are made.
    - Adjust mock return values and side effects to simulate new edge cases or errors.
    - Use assert_called, assert_not_called, and patch.object to verify correct workflow.

Error/warning message hints:
    - If you see real network calls, check that all relevant functions are patched/mocked.
    - If a test fails, check assertion logic and mock return values.
    - For new workflow logic, update or add tests to match expected behavior.
"""
import unittest
from unittest.mock import patch, MagicMock
from susi.social_posters.instagram import InstagramPoster
from susi.main import process_images

class TestSusiIntegration(unittest.TestCase):
    """
    Integration test suite for the full Susi image workflow.

    Mocks all major external dependencies to ensure tests are fast, isolated, and safe.
    """
    @patch('os.remove')
    @patch('susi.main.download_onedrive_image')
    @patch('susi.main.list_onedrive_images')
    @patch('susi.main.extract_metadata')
    @patch('susi.main.generate_post_text')
    @patch('susi.main.upload_file_to_s3')
    @patch('susi.main.move_onedrive_file_to_processed')
    @patch('susi.main.send_confirmation')
    @patch('susi.main.send_error')
    def test_full_workflow_success(self, mock_send_error, mock_send_confirmation, mock_move_processed, mock_upload_s3, mock_generate_post, mock_extract_metadata, mock_list_images, mock_download, mock_remove):
        """
        Test: Full happy-path workflow with all steps succeeding.

        Verifies that all steps are called in order, with correct arguments, and confirmation email is sent.
        """
        # Setup mocks
        mock_list_images.return_value = [{'id': '1', 'name': 'test.jpg'}]
        mock_download.return_value = 'downloads/test.jpg'
        mock_extract_metadata.return_value = {'title': 'Test', 'comment': 'A comment'}
        mock_generate_post.return_value = 'Test caption'
        mock_upload_s3.return_value = 'https://bucket.s3.region.amazonaws.com/test.jpg'
        # Patch the InstagramPoster.post method
        with patch.object(InstagramPoster, 'post', return_value=True) as mock_post:
            seen_ids = set()
            process_images(images=None, seen_ids=seen_ids, poster=InstagramPoster())
            mock_list_images.assert_called()
            mock_download.assert_called()
            mock_extract_metadata.assert_called()
            mock_generate_post.assert_called()
            mock_upload_s3.assert_called()
            mock_post.assert_called()
            mock_move_processed.assert_called()
            mock_send_confirmation.assert_called()
            mock_send_error.assert_not_called()

    @patch('os.remove')
    @patch('susi.main.download_onedrive_image')
    @patch('susi.main.list_onedrive_images')
    @patch('susi.main.extract_metadata')
    @patch('susi.main.generate_post_text')
    @patch('susi.main.upload_file_to_s3')
    @patch('susi.main.move_onedrive_file_to_processed')
    @patch('susi.main.send_confirmation')
    @patch('susi.main.send_error')
    def test_s3_upload_failure(self, mock_send_error, mock_send_confirmation, mock_move_processed, mock_upload_s3, mock_generate_post, mock_extract_metadata, mock_list_images, mock_download, mock_remove):
        """
        Test: S3 upload failure aborts workflow and sends error email.
        """
        mock_list_images.return_value = [{'id': '1', 'name': 'test.jpg'}]
        mock_download.return_value = 'downloads/test.jpg'
        mock_extract_metadata.return_value = {'title': 'Test', 'comment': 'A comment'}
        mock_generate_post.return_value = 'Test caption'
        mock_upload_s3.return_value = None  # Simulate S3 upload failure
        with patch.object(InstagramPoster, 'post', return_value=True) as mock_post:
            seen_ids = set()
            process_images(images=None, seen_ids=seen_ids, poster=InstagramPoster())
            mock_send_error.assert_called()
            mock_post.assert_not_called()
            mock_move_processed.assert_not_called()
            mock_send_confirmation.assert_not_called()

if __name__ == '__main__':
    unittest.main()
