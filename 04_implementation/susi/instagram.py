
"""
instagram.py: Handles posting images to Instagram using the Instagram Graph API.

Features:
    - Posts images with captions to Instagram via the Graph API.
    - Uses retry logic for robust posting.

Developer hints:
    - Requires valid Instagram Graph API credentials (access_token, user_id) in config.
    - If you see API errors, check your access token, user ID, and image URL accessibility.
    - Use logging to trace errors and workflow steps.

Error/warning message hints:
    - If you see 'Failed to create media object', check the image URL and access token.
    - If you see 'No creation_id returned', the media object was not created—check API response for details.
    - If you see 'Failed to publish media', check API permissions and creation_id validity.
    - Always log the full API response for troubleshooting.
"""

import logging
import requests
import time
from .retry_utils import retry
from typing import Dict

@retry(Exception, tries=3, delay=2, backoff=2, logger=logging.getLogger("susi.main"))
def wait_for_media_ready(creation_id: str, access_token: str, max_wait: int = 60, poll_interval: int = 5) -> bool:
    """
    Poll the Instagram API for media processing status until ready or timeout.
    Returns True if ready, False if error or timeout.
    """
    url = f"https://graph.facebook.com/v19.0/{creation_id}?fields=status_code&access_token={access_token}"
    waited = 0
    while waited < max_wait:
        try:
            resp = requests.get(url)
            data = resp.json()
            status = data.get("status_code")
            if status == "FINISHED":
                return True
            elif status == "ERROR":
                logging.error(f"Instagram media processing failed: {data}")
                return False
        except Exception as e:
            logging.error(f"Error polling Instagram media status: {e}")
        time.sleep(poll_interval)
        waited += poll_interval
    logging.error("Timeout waiting for Instagram media to be ready.")
    return False


@retry(Exception, tries=3, delay=2, backoff=2, logger=logging.getLogger("susi.main"))
def post_to_instagram(image_url: str, caption: str, config: Dict) -> bool:
    """
    Post an image to Instagram using the Instagram Graph API.

    Args:
        image_url (str): Public URL of the image to post.
        caption (str): Caption for the Instagram post.
        config (dict): Instagram configuration with 'access_token' and 'user_id'.

    Returns:
        bool: True if the post was successful, False otherwise.

    Raises:
        KeyError: If required config keys are missing.
        requests.RequestException: If the API call fails (caught by retry logic).

    Developer hint:
        - This function is retried on failure (see retry decorator).
        - Log all errors and API responses for debugging.
        - If you see repeated failures, check API credentials and permissions.

    Workflow:
        1. Create a media object with the image and caption.
        2. Publish the media object to the Instagram feed.
    """

    # Extract credentials from config
    access_token = config['instagram']['access_token']
    user_id = config['instagram']['user_id']

    # Step 1: Create media object
    create_url = f"https://graph.facebook.com/v19.0/{user_id}/media"
    payload = {
        'image_url': image_url,
        'caption': caption,
        'access_token': access_token
    }
    resp = requests.post(create_url, data=payload)
    if resp.status_code != 200:
        logging.error(f"Failed to create media object: {resp.text}")
        return False
    creation_id = resp.json().get('id')
    if not creation_id:
        logging.error(f"No creation_id returned from Instagram: {resp.text}")
        return False

    # Step 2: Poll for media readiness
    if not wait_for_media_ready(creation_id, access_token, max_wait=60, poll_interval=5):
        logging.error(f"Media object {creation_id} not ready for publishing after waiting.")
        return False

    # Step 3: Publish media object
    publish_url = f"https://graph.facebook.com/v19.0/{user_id}/media_publish"
    payload = {
        'creation_id': creation_id,
        'access_token': access_token
    }
    resp = requests.post(publish_url, data=payload)
    if resp.status_code != 200:
        logging.error(f"Failed to publish media: {resp.text}")
        return False
    logging.info(f"Successfully posted image to Instagram: {image_url}")
    return True
