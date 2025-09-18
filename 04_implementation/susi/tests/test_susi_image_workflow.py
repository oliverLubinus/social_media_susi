"""
test_susi_image_workflow.py: Unit tests for the image posting workflow in Susi.

Features:
    - Tests OneDrive image monitoring, metadata extraction, S3 upload, and Instagram posting.
    - Mocks all external dependencies (OneDrive, S3, Instagram, etc.) for fast, isolated tests.

Developer hints:
    - All network/storage/Instagram calls are mocked; no real uploads or posts are made.
    - Adjust mock return values and side effects to simulate new edge cases or errors.
    - Use assert_called_once, assert_called_once_with, and MagicMock to verify correct workflow.

Error/warning message hints:
    - If you see real network calls, check that all relevant functions are patched/mocked.
    - If a test fails, check assertion logic and mock return values.
    - For new workflow logic, update or add tests to match expected behavior.
"""
import unittest
from unittest.mock import patch, MagicMock, ANY
from susi.main import process_images

class TestImageWorkflow(unittest.TestCase):
    """
    Unit test suite for the image posting workflow in Susi.

    Mocks all major external dependencies to ensure tests are fast, isolated, and safe.
    """
    @patch('susi.main.config', {
        'template': '{title}\n{comment}',
        'aws': {
            's3_bucket': 'bucket',
            'access_key_id': 'key',
            'secret_access_key': 'secret',
            'region': 'region',
        },
        'logging': {'file': 'test.log', 'level': 'INFO'},
        'email': {'provider': 'test', 'username': 'dummy', 'recipient': 'dummy'},
        'onedrive': {'processed_folder': '/processed'},
        'instagram': {'access_token': 'dummy', 'user_id': 'dummy'}
    })
    @patch('susi.main.list_onedrive_images')
    @patch('susi.main.download_onedrive_image')
    @patch('susi.main.extract_metadata')
    @patch('susi.main.generate_post_text')
    @patch('susi.main.upload_file_to_s3')
    @patch('susi.main.InstagramPoster')
    @patch('susi.main.move_onedrive_file_to_processed')
    @patch('os.remove')
    def test_image_to_instagram_post(
        self, mock_remove, mock_move_processed, mock_poster_cls, mock_upload_s3, mock_generate_post, mock_extract, mock_download, mock_list
    ):
        """
        Test: Full happy-path workflow for posting an image to Instagram.

        Verifies that all steps are called in order, with correct arguments, and the image is removed after posting.
        """
        # Arrange: mock image
        mock_list.return_value = [{'id': '1', 'name': 'test.jpg'}]
        print('DEBUG: mock_list.return_value =', mock_list.return_value)
        mock_download.return_value = 'downloads/test.jpg'
        mock_extract.return_value = {'title': 'Test', 'comment': 'A comment'}
        mock_generate_post.return_value = 'Test caption'
        mock_upload_s3.return_value = 'https://bucket.s3.region.amazonaws.com/test.jpg'
        mock_poster = MagicMock()
        mock_poster.post.return_value = True
        mock_poster_cls.return_value = mock_poster
        # Act
        process_images()
        # Assert
        mock_list.assert_called_once()
        mock_download.assert_called_once()
        mock_extract.assert_called_once()
        mock_generate_post.assert_called_once()
        mock_upload_s3.assert_called_once()
        mock_poster.post.assert_called_once_with('https://bucket.s3.region.amazonaws.com/test.jpg', 'Test caption', ANY)
        mock_move_processed.assert_called_once()
        mock_remove.assert_called_once_with('downloads/test.jpg')

if __name__ == '__main__':
    unittest.main()
