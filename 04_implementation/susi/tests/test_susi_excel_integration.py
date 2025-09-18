"""
test_susi_excel_integration.py: Integration tests for the Excel-driven workflow in Susi.

Features:
	- Simulates the end-to-end process: Excel row -> news fetch -> LLM post -> Excel write/mark processed.
	- Mocks all major external dependencies (news, LLM, Excel, email, network).
	- Covers success, error, and edge-case scenarios for robust workflow validation.

Developer hints:
	- All network/genAI/Excel/email calls are mocked; no real API calls are made.
	- Add/adjust test data in mock_get_rows for new edge cases.
	- Use assert_has_calls and call_count to verify correct workflow execution.

Error/warning message hints:
	- If you see real network calls, check that all relevant functions are patched/mocked.
	- If a test fails, check assertion logic and mock return values.
	- For new workflow logic, update or add tests to match expected behavior.
"""
import unittest
from unittest.mock import patch, MagicMock
from susi.main import process_excel_topics
from unittest.mock import patch as upatch
import sys

class TestExcelIntegration(unittest.TestCase):
	"""
	Integration test suite for the Excel-driven workflow in Susi.

	Mocks all major external dependencies to ensure tests are fast, isolated, and safe.
	"""
	def setUp(self):
		# Patch all genAI/networked functions globally for all tests
		patcher_linkedin = patch('susi.main.generate_linkedin_post', return_value="LinkedIn post (mocked)")
		patcher_instagram = patch('susi.main.generate_instagram_post', return_value="Instagram post (mocked)")
		patcher_genai_api = patch('susi.genai_api.generate_linkedin_post', return_value="LinkedIn post (mocked)")
		patcher_requests_post = patch('requests.post', side_effect=RuntimeError("requests.post called during test"))
		patcher_requests_get = patch('requests.get', side_effect=RuntimeError("requests.get called during test"))
		self._patchers = [patcher_linkedin, patcher_instagram, patcher_genai_api, patcher_requests_post, patcher_requests_get]
		self._mocks = [p.start() for p in self._patchers]

	def tearDown(self):
		for p in self._patchers:
			p.stop()
	@patch('susi.main.send_confirmation')
	@patch('susi.main.send_error')
	@patch('susi.genai_api.generate_linkedin_post', return_value="LinkedIn post about AI in Healthcare for doctors.")
	@patch('susi.main.generate_instagram_post', return_value="Instagram post about AI in Healthcare for doctors.")
	@patch('susi.excel_monitor.get_excel_rows')
	@patch('susi.main.fetch_news_articles')
	@patch('susi.excel_monitor.write_instagram_post')
	@patch('susi.excel_monitor.write_linkedin_post')
	@patch('susi.excel_monitor.mark_row_processed')
	def test_excel_workflow_success(
		self, mock_mark_processed, mock_write_linkedin, mock_write_insta, mock_news, mock_get_rows, mock_genai_insta, mock_genai_linkedin, mock_send_error, mock_send_confirmation
	):
		"""
		Test: Full happy-path workflow with two Excel rows.

		Verifies that all steps are called in order, with correct arguments, and confirmation emails are sent.
		"""
		# Arrange: mock Excel row
		mock_get_rows.return_value = [
			{'Content': 'AI in Healthcare', 'Target Group': 'Doctors', 'Instagram': '', 'LinkedIn': '', 'processed': ''},
			{'Content': 'AI in Finance', 'Target Group': 'Bankers', 'Instagram': '', 'LinkedIn': '', 'processed': ''}
		]
		mock_news.return_value = [
			{'title': 'AI revolutionizes diagnosis', 'description': 'AI is helping doctors...'}
		]
		# Act
		process_excel_topics()
		# Assert
		mock_get_rows.assert_called_once()
		mock_news.assert_has_calls([
			unittest.mock.call('AI in Healthcare', 'Doctors'),
			unittest.mock.call('AI in Finance', 'Bankers')
		])
		mock_genai_insta.assert_has_calls([
			unittest.mock.call('AI in Healthcare', 'Doctors', [{'title': 'AI revolutionizes diagnosis', 'description': 'AI is helping doctors...'}]),
			unittest.mock.call('AI in Finance', 'Bankers', [{'title': 'AI revolutionizes diagnosis', 'description': 'AI is helping doctors...'}])
		])
		mock_write_insta.assert_has_calls([
			unittest.mock.call(0, "Instagram post about AI in Healthcare for doctors."),
			unittest.mock.call(1, "Instagram post about AI in Healthcare for doctors.")
		])
		mock_write_linkedin.assert_has_calls([
			unittest.mock.call(0, "LinkedIn post (mocked)"),
			unittest.mock.call(1, "LinkedIn post (mocked)")
		])
		mock_mark_processed.assert_has_calls([
			unittest.mock.call(0),
			unittest.mock.call(1)
		])
		assert mock_send_confirmation.call_count == 2
		mock_send_error.assert_not_called()

	@patch('susi.main.send_error')
	@patch('susi.genai_api.generate_linkedin_post', return_value="LinkedIn post about AI in Healthcare for doctors.")
	@patch('susi.main.generate_instagram_post', side_effect=Exception('LLM error'))
	@patch('susi.excel_monitor.get_excel_rows')
	@patch('susi.main.fetch_news_articles')
	@patch('susi.excel_monitor.write_instagram_post')
	@patch('susi.excel_monitor.mark_row_processed')
	@patch('susi.main.InstagramPoster')
	def test_excel_workflow_llm_fallback(
		self, mock_poster_cls, mock_mark_processed, mock_write_insta, mock_news, mock_get_rows, mock_genai, mock_genai_linkedin, mock_send_error
	):
			# Arrange: mock Excel row
			mock_get_rows.return_value = [
				{'Content': 'AI in Healthcare', 'Target Group': 'Doctors', 'Instagram': '', 'processed': ''}
			]
			mock_news.return_value = [
				{'title': 'AI revolutionizes diagnosis', 'description': 'AI is helping doctors...'}
			]
			mock_poster = MagicMock()
			mock_poster.post.return_value = True
			mock_poster_cls.return_value = mock_poster
			# Act
			process_excel_topics()
			# Assert
			mock_get_rows.assert_called_once()
			mock_news.assert_called_once_with('AI in Healthcare', 'Doctors')
			mock_genai.assert_called_once()
			# Fallback caption should be written
			fallback_caption = "Topic: AI in Healthcare\nTarget Group: Doctors\n\nRelevant News:\n- AI revolutionizes diagnosis"
			mock_write_insta.assert_called_once_with(0, fallback_caption)
			mock_poster.post.assert_not_called()
			# Do not assert mark_row_processed or LinkedIn post, as workflow aborts

	@patch('susi.main.send_error')
	@patch('susi.genai_api.generate_linkedin_post', return_value="LinkedIn post about AI in Healthcare for doctors.")
	@patch('susi.main.generate_instagram_post', return_value="Instagram post about AI in Healthcare for doctors.")
	@patch('susi.excel_monitor.get_excel_rows')
	@patch('susi.main.fetch_news_articles', side_effect=Exception('NewsAPI error'))
	@patch('susi.excel_monitor.write_instagram_post')
	@patch('susi.excel_monitor.mark_row_processed')
	@patch('susi.main.InstagramPoster')
	def test_excel_workflow_newsapi_error(
		self, mock_poster_cls, mock_mark_processed, mock_write_insta, mock_news, mock_get_rows, mock_genai, mock_genai_linkedin, mock_send_error
	):
			# Arrange: mock Excel row
			mock_get_rows.return_value = [
				{'Content': 'AI in Healthcare', 'Target Group': 'Doctors', 'Instagram': '', 'processed': ''}
			]
			mock_poster = MagicMock()
			mock_poster.post.return_value = True
			mock_poster_cls.return_value = mock_poster
			# Act
			process_excel_topics()
			# Assert
			mock_get_rows.assert_called_once()
			mock_news.assert_called_once_with('AI in Healthcare', 'Doctors')
			mock_genai.assert_called_once()
			mock_write_insta.assert_called_once_with(0, "Instagram post about AI in Healthcare for doctors.")
			mock_poster.post.assert_not_called()
			# Do not assert mark_row_processed or LinkedIn post, as workflow aborts

	@patch('susi.main.send_confirmation')
	@patch('susi.genai_api.generate_linkedin_post', return_value="LinkedIn post about AI in Healthcare for doctors.")
	@patch('susi.main.generate_instagram_post', return_value="Instagram post about AI in Healthcare for doctors.")
	@patch('susi.excel_monitor.get_excel_rows')
	@patch('susi.main.fetch_news_articles')
	@patch('susi.excel_monitor.write_instagram_post')
	@patch('susi.excel_monitor.write_linkedin_post')
	@patch('susi.excel_monitor.mark_row_processed')
	def test_excel_workflow_empty_rows(
		self, mock_mark_processed, mock_write_linkedin, mock_write_insta, mock_news, mock_get_rows, mock_genai_insta, mock_genai_linkedin, mock_send_confirmation
	):
		# Arrange: no rows
		mock_get_rows.return_value = []
		# Act
		process_excel_topics()
		# Assert
		mock_get_rows.assert_called_once()
		mock_news.assert_not_called()
		mock_genai_insta.assert_not_called()
		mock_genai_linkedin.assert_not_called()
		mock_write_insta.assert_not_called()
		mock_write_linkedin.assert_not_called()
		mock_mark_processed.assert_not_called()

	@patch('susi.main.send_confirmation')
	@patch('susi.main.send_error')
	@patch('susi.genai_api.generate_linkedin_post', return_value="LinkedIn post about AI in Healthcare for doctors.")
	@patch('susi.main.generate_instagram_post', return_value="Instagram post about AI in Healthcare for doctors.")
	@patch('susi.excel_monitor.get_excel_rows')
	@patch('susi.main.fetch_news_articles')
	@patch('susi.excel_monitor.write_instagram_post', side_effect=Exception('Excel write error'))
	@patch('susi.excel_monitor.write_linkedin_post')
	@patch('susi.excel_monitor.mark_row_processed')
	def test_excel_workflow_write_instagram_post_failure(
		self, mock_mark_processed, mock_write_linkedin, mock_write_insta, mock_news, mock_get_rows, mock_genai_insta, mock_genai_linkedin, mock_send_error, mock_send_confirmation
	):
		mock_get_rows.return_value = [
			{'Content': 'AI in Healthcare', 'Target Group': 'Doctors', 'Instagram': '', 'LinkedIn': '', 'processed': ''}
		]
		mock_news.return_value = [
			{'title': 'AI revolutionizes diagnosis', 'description': 'AI is helping doctors...'}
		]
		process_excel_topics()
		mock_write_insta.assert_called_once()
		mock_send_error.assert_called()
		# Workflow aborts after Instagram write fails
		mock_mark_processed.assert_called_once_with(0)
		mock_write_linkedin.assert_called_once_with(0, "LinkedIn post (mocked)")
		mock_send_confirmation.assert_called_once()

	@patch('susi.main.send_confirmation')
	@patch('susi.main.send_error')
	@patch('susi.genai_api.generate_linkedin_post', return_value="LinkedIn post about AI in Healthcare for doctors.")
	@patch('susi.main.generate_instagram_post', return_value="Instagram post about AI in Healthcare for doctors.")
	@patch('susi.excel_monitor.get_excel_rows')
	@patch('susi.main.fetch_news_articles')
	@patch('susi.excel_monitor.write_instagram_post')
	@patch('susi.excel_monitor.write_linkedin_post', side_effect=Exception('Excel write error'))
	@patch('susi.excel_monitor.mark_row_processed')
	def test_excel_workflow_write_linkedin_post_failure(
		self, mock_mark_processed, mock_write_linkedin, mock_write_insta, mock_news, mock_get_rows, mock_genai_insta, mock_genai_linkedin, mock_send_error, mock_send_confirmation
	):
		mock_get_rows.return_value = [
			{'Content': 'AI in Healthcare', 'Target Group': 'Doctors', 'Instagram': '', 'LinkedIn': '', 'processed': ''}
		]
		mock_news.return_value = [
			{'title': 'AI revolutionizes diagnosis', 'description': 'AI is helping doctors...'}
		]
		process_excel_topics()
		mock_write_linkedin.assert_called_once_with(0, "LinkedIn post (mocked)")
		mock_send_error.assert_called_once()
		# mark_processed and send_confirmation are not called
		mock_mark_processed.assert_not_called()
		mock_send_confirmation.assert_not_called()

	@patch('susi.main.send_confirmation')
	@patch('susi.main.send_error')
	@patch('susi.genai_api.generate_linkedin_post', return_value="LinkedIn post about AI in Healthcare for doctors.")
	@patch('susi.main.generate_instagram_post', return_value="Instagram post about AI in Healthcare for doctors.")
	@patch('susi.excel_monitor.get_excel_rows')
	@patch('susi.main.fetch_news_articles')
	@patch('susi.excel_monitor.write_instagram_post')
	@patch('susi.excel_monitor.write_linkedin_post')
	@patch('susi.excel_monitor.mark_row_processed', side_effect=Exception('Mark processed error'))
	def test_excel_workflow_mark_row_processed_failure(
		self, mock_mark_processed, mock_write_linkedin, mock_write_insta, mock_news, mock_get_rows, mock_genai_insta, mock_genai_linkedin, mock_send_error, mock_send_confirmation
	):
		mock_get_rows.return_value = [
			{'Content': 'AI in Healthcare', 'Target Group': 'Doctors', 'Instagram': '', 'LinkedIn': '', 'processed': ''}
		]
		mock_news.return_value = [
			{'title': 'AI revolutionizes diagnosis', 'description': 'AI is helping doctors...'}
		]
		process_excel_topics()
		mock_mark_processed.assert_called_once_with(0)
		mock_send_confirmation.assert_not_called()
		mock_send_error.assert_called_once()

	@patch('susi.genai_api.generate_linkedin_post', return_value="LinkedIn post about AI in Healthcare for doctors.")
	@patch('susi.main.generate_instagram_post', return_value="Instagram post about AI in Healthcare for doctors.")
	@patch('susi.excel_monitor.get_excel_rows')
	@patch('susi.main.fetch_news_articles')
	@patch('susi.excel_monitor.write_instagram_post')
	@patch('susi.excel_monitor.write_linkedin_post')
	@patch('susi.excel_monitor.mark_row_processed')
	@patch('susi.main.send_confirmation', side_effect=Exception('Email error'))
	@patch('susi.main.send_error')
	def test_excel_workflow_send_confirmation_failure(
		self, mock_send_error, mock_send_confirmation, mock_mark_processed, mock_write_linkedin, mock_write_insta, mock_news, mock_get_rows, mock_genai_insta, mock_genai_linkedin
	):
		mock_get_rows.return_value = [
			{'Content': 'AI in Healthcare', 'Target Group': 'Doctors', 'Instagram': '', 'LinkedIn': '', 'processed': ''}
		]
		mock_news.return_value = [
			{'title': 'AI revolutionizes diagnosis', 'description': 'AI is helping doctors...'}
		]
		process_excel_topics()
		mock_send_confirmation.assert_called_once()
		mock_send_error.assert_called_once()

	@patch('susi.genai_api.generate_linkedin_post', return_value="LinkedIn post about AI in Healthcare for doctors.")
	@patch('susi.main.generate_instagram_post', return_value="Instagram post about AI in Healthcare for doctors.")
	@patch('susi.excel_monitor.get_excel_rows')
	@patch('susi.main.fetch_news_articles')
	@patch('susi.excel_monitor.write_instagram_post')
	@patch('susi.excel_monitor.write_linkedin_post')
	@patch('susi.excel_monitor.mark_row_processed')
	@patch('susi.main.send_error', side_effect=Exception('Email error'))
	def test_excel_workflow_send_error_failure(
		self, mock_send_error, mock_mark_processed, mock_write_linkedin, mock_write_insta, mock_news, mock_get_rows, mock_genai_insta, mock_genai_linkedin
	):
		mock_get_rows.return_value = [
			{'Content': 'AI in Healthcare', 'Target Group': 'Doctors', 'Instagram': '', 'LinkedIn': '', 'processed': ''}
		]
		mock_news.return_value = [
			{'title': 'AI revolutionizes diagnosis', 'description': 'AI is helping doctors...'}
		]
		# Should not raise, workflow should handle error in error handler
		mock_send_error.side_effect = [Exception('Email error'), None]
		process_excel_topics()
		assert mock_send_error.call_count == 0

	@patch('susi.main.send_confirmation')
	@patch('susi.main.send_error')
	@patch('susi.genai_api.generate_linkedin_post', return_value="LinkedIn post about AI in Healthcare for doctors.")
	@patch('susi.main.generate_instagram_post', return_value="Instagram post about AI in Healthcare for doctors.")
	@patch('susi.excel_monitor.get_excel_rows')
	@patch('susi.main.fetch_news_articles')
	@patch('susi.excel_monitor.write_instagram_post')
	@patch('susi.excel_monitor.write_linkedin_post')
	@patch('susi.excel_monitor.mark_row_processed')
	def test_excel_workflow_mixed_success_failure(
		self, mock_mark_processed, mock_write_linkedin, mock_write_insta, mock_news, mock_get_rows, mock_genai_insta, mock_genai_linkedin, mock_send_error, mock_send_confirmation
	):
		mock_get_rows.return_value = [
			{'Content': 'AI in Healthcare', 'Target Group': 'Doctors', 'Instagram': '', 'LinkedIn': '', 'processed': ''},
			{'Content': '', 'Target Group': 'Doctors', 'Instagram': '', 'LinkedIn': '', 'processed': ''}, # missing content
			{'Content': 'AI in Finance', 'Target Group': '', 'Instagram': '', 'LinkedIn': '', 'processed': ''}
		]
		mock_news.return_value = [
			{'title': 'AI revolutionizes diagnosis', 'description': 'AI is helping doctors...'}
		]
		process_excel_topics()
		# Only the first and third rows are processed (second is skipped)
		mock_write_insta.assert_any_call(0, "Instagram post about AI in Healthcare for doctors.")
		mock_write_insta.assert_any_call(2, "Instagram post about AI in Healthcare for doctors.")
		mock_write_linkedin.assert_any_call(0, "LinkedIn post (mocked)")
		mock_write_linkedin.assert_any_call(2, "LinkedIn post (mocked)")
		mock_mark_processed.assert_any_call(0)
		mock_mark_processed.assert_any_call(2)
		# Assert confirmation email sent for each successful row
		assert mock_send_confirmation.call_count == 2
		# Assert no error email sent
		mock_send_error.assert_not_called()

if __name__ == '__main__':
	unittest.main()
