"""
test_e2e_image_workflow.py: End-to-end tests for the Susi image workflow using real credentials and live external services.

Features:
    - Runs the full image workflow with real API calls (no mocks).
    - Validates integration of OneDrive/S3, image processing, and social posting.

Developer hints:
    - Set all required environment variables for credentials before running.
    - These tests are slow and may have side effects (real uploads, posts, S3/OneDrive changes).
    - Use only when you want to validate the full production pipeline.

Error/warning message hints:
    - If you see authentication or permission errors, check your environment variables and config.
    - If you see unexpected uploads/posts, clean up manually after test runs.
    - Use with caution: these tests are not isolated and may affect real data.

To run: set all required environment variables for credentials, and run this file explicitly.

WARNING: These tests may upload real images, post to real social accounts, and use real S3/OneDrive buckets.
"""
import os
import unittest
from susi.main import process_images


@unittest.skipUnless(os.environ.get("E2E_TESTS") == "1", "E2E tests are only run when E2E_TESTS=1 is set.")
class TestSusiImageE2E(unittest.TestCase):
    def test_image_workflow_real_services(self):
        """
        Runs the full image workflow with real credentials and services.

        Expects:
            - All environment variables and config are set for real API access.
            - Test image(s) are present in OneDrive or S3, or set up before running.

        Developer hints:
            - Optionally, set up test image(s) in OneDrive or S3 before running.
            - Optionally, clean up or verify state before/after running.
            - Add assertions to check for expected side effects (uploads, posts, S3/OneDrive changes).
            - For true E2E, manual verification may be required, or automate checks via APIs.
        """
        # Optionally, set up test image(s) in OneDrive or S3 here (or ensure test data is present)
        # Optionally, clean up or verify state before running
        process_images()
        # Optionally, add assertions to check for expected side effects (e.g., S3 uploads, social posts)
        # For true E2E, manual verification may be required, or you can automate checks via APIs

if __name__ == "__main__":
    unittest.main()
