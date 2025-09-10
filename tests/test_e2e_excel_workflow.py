"""
test_e2e_excel_workflow.py: End-to-end tests for the Susi Excel-driven workflow using real credentials and live external services.

Features:
    - Runs the full Excel-driven workflow with real API calls (no mocks).
    - Validates integration of Excel, news, LLM, email, and social posting.

Developer hints:
    - Set all required environment variables for credentials before running.
    - These tests are slow and may have side effects (real posts, emails, Excel edits).
    - Use only when you want to validate the full production pipeline.

Error/warning message hints:
    - If you see authentication or permission errors, check your environment variables and config.
    - If you see unexpected posts/emails, clean up manually after test runs.
    - Use with caution: these tests are not isolated and may affect real data.

To run: set all required environment variables for credentials, and run this file explicitly.

WARNING: These tests may create real posts, send real emails, and modify real Excel files.
"""
import os
import unittest
from susi.main import process_excel_topics


@unittest.skipUnless(os.environ.get("E2E_TESTS") == "1", "E2E tests are only run when E2E_TESTS=1 is set.")
class TestSusiE2E(unittest.TestCase):
    def test_excel_workflow_real_services(self):
        """
        Runs the full Excel-driven workflow with real credentials and services.

        Expects:
            - All environment variables and config are set for real API access.
            - Test data is present in Excel, or set up before running.

        Developer hints:
            - Optionally, set up test data in Excel before running.
            - Optionally, clean up or verify state before/after running.
            - Add assertions to check for expected side effects (posts, emails, Excel changes).
            - For true E2E, manual verification may be required, or automate checks via APIs.
        """
        # Optionally, set up test data in Excel here (or ensure test data is present)
        # Optionally, clean up or verify state before running
        process_excel_topics()
        # Optionally, add assertions to check for expected side effects (e.g., posts, emails, Excel changes)
        # For true E2E, manual verification may be required, or you can automate checks via APIs

if __name__ == "__main__":
    unittest.main()
