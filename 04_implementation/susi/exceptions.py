
"""
Custom exception classes for the Susi social media agent.

Use these exceptions to provide clear, actionable error handling for key workflow failures.

Developer hints:
    - Raise these exceptions in your code to signal specific error conditions.
    - Catch these exceptions at workflow boundaries to trigger error emails, logging, or retries.
    - Include a descriptive error message when raising for easier debugging.

Error/warning message hints:
    - When catching these exceptions, log the error message and provide hints for resolution (e.g., check credentials, network, permissions).
    - If you see these errors in logs, check the associated stack trace and error message for root cause.
"""


class OneDriveDownloadError(Exception):
    """
    Raised when a OneDrive file download fails.

    Developer hint:
        - Check your OneDrive API credentials, file path, and network connectivity.
        - Log the full exception message for troubleshooting.
    """
    pass


class S3UploadError(Exception):
    """
    Raised when an S3 upload fails.

    Developer hint:
        - Check your AWS credentials, S3 bucket name, permissions, and network.
        - Log the full exception message for troubleshooting.
    """
    pass


class InstagramPostError(Exception):
    """
    Raised when posting to Instagram fails.

    Developer hint:
        - Check your Instagram API credentials, access token, permissions, and image/media requirements.
        - Log the full exception message for troubleshooting.
    """
    pass
