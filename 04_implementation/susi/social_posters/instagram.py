
"""
InstagramPoster implements the SocialPoster interface for posting to Instagram.
"""

import logging
from typing import Dict
from ..instagram import post_to_instagram
from .base import SocialPoster

class InstagramPoster(SocialPoster):
    """
    SocialPoster implementation for Instagram.

    Developer hint:
        - This class implements the SocialPoster interface for Instagram.
        - To test without posting, use the dry_run argument.
        - All errors from the Instagram API are logged; check logs for troubleshooting tips.
    """

    def post(self, image_url: str, caption: str, config: Dict, dry_run: bool = False) -> bool:
        """
        Post an image with a caption to Instagram.

        Args:
            image_url (str): Public URL of the image to post.
            caption (str): Caption or description for the post.
            config (dict): Instagram-specific configuration and credentials.
            dry_run (bool): If True, do not actually post—just log intent (for testing).

        Returns:
            bool: True if the post was successful, False otherwise.

        Warning:
            - If the post fails, check the logs for error messages from the Instagram API.
            - Common issues: invalid access token, missing permissions, image URL not accessible, API rate limits.
        """
        # If dry_run is enabled, log the intent and skip the actual post
        if dry_run:
            logging.info(f"[DRY RUN][InstagramPoster] Would post to Instagram: {image_url}")
            return True
        # Log the posting action for traceability
        logging.info(f"[InstagramPoster] Posting to Instagram: {image_url}")
        # Delegate to the actual Instagram posting function
        return post_to_instagram(image_url, caption, config)
