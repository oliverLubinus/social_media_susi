
"""
Base class for all social media poster implementations in Susi.
To add support for a new platform, inherit from SocialPoster and implement the post method.
"""

from abc import ABC, abstractmethod

class SocialPoster(ABC):
    """
    Abstract base class for posting images and captions to social media platforms.

    Developer hint:
        - To add support for a new platform, inherit from SocialPoster and implement the post() method.
        - The post() method should handle all platform-specific API logic and error handling.
        - Always return True for success, False for failure. Do not raise exceptions unless absolutely necessary.
        - Log errors and warnings with actionable hints for debugging (e.g., check credentials, API limits).
    """

    @abstractmethod
    def post(self, image_url: str, caption: str, config: dict) -> bool:
        """
        Post an image with a caption to the social platform.

        Args:
            image_url (str): Public URL of the image to post.
            caption (str): Caption or description for the post.
            config (dict): Platform-specific configuration and credentials.

        Returns:
            bool: True if the post was successful, False otherwise.

        Warning:
            - Implementations should catch and log all exceptions, returning False on failure.
            - If the API returns an error, log the error message and provide hints (e.g., check access token, permissions, API limits).
        """
        # Subclasses must implement this method for their specific platform.
        pass
