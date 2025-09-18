
"""
onedrive_monitor.py: Utilities for monitoring and managing images in a OneDrive folder for Susi.

Features:
    - Lists image files in a configured OneDrive folder using Microsoft Graph API.
    - Downloads images from OneDrive to a local directory.
    - Moves processed images to a separate folder with timestamped filenames.

Developer hints:
    - Requires valid OneDrive OAuth2 credentials and config.yaml (or SUSI_CONFIG env var).
    - All configuration and environment variable resolution is handled via centralized helpers in config.py.
    - All OneDrive API calls are retried on failure (see @retry decorator) using the centralized "susi.main" logger.
    - If you see token or permission errors, check your OAuth2 setup and folder permissions.

Error/warning message hints:
    - If you see 'No token found', run the OAuth2 flow to obtain a new token.
    - If you see 'requests.exceptions.HTTPError', check your access token and folder path.
    - Always check logs for details on download/move failures.
"""

from datetime import datetime

from dotenv import load_dotenv
from .onedrive_auth import get_access_token
from .retry_utils import retry
from typing import List, Dict, Any
import os
import shutil
import logging
import requests

# Use config helpers and constants
from .config import get_config, ONEDRIVE_KEY

load_dotenv()
config = get_config()

ONEDRIVE_FOLDER_PATH = config[ONEDRIVE_KEY]['folder']  # e.g. "/drive/root:/SusiImages"
LOCAL_DOWNLOAD_DIR = config[ONEDRIVE_KEY].get('local_download_dir', 'downloads')


@retry(Exception, tries=3, delay=2, backoff=2, logger=logging.getLogger("susi.main"))
def list_onedrive_images() -> List[Dict[str, Any]]:
    """
    List image files in the configured OneDrive folder using Microsoft Graph API.

    Returns:
        List[dict]: List of OneDrive file metadata dicts for images.

    Developer hints:
        - Only files with supported image extensions are returned.
        - If you see HTTP 401/403 errors, check your access token and folder permissions.
        - Retries up to 3 times on transient errors (see @retry).
    """
    access_token = get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    supported_ext = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
    # List items in the folder
    url = f"https://graph.microsoft.com/v1.0/me/drive/root:{ONEDRIVE_FOLDER_PATH}:/children"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    items = resp.json().get('value', [])
    image_files = [item for item in items if any(item['name'].lower().endswith(ext) for ext in supported_ext)]
    return image_files


@retry(Exception, tries=3, delay=2, backoff=2, logger=logging.getLogger("susi.main"))
def download_onedrive_image(item: Dict[str, Any]) -> str:
    """
    Download an image file from OneDrive to the local download directory.

    Args:
        item (dict): OneDrive file metadata dict (from list_onedrive_images).

    Returns:
        str: Local path to the downloaded image file.

    Developer hints:
        - Creates the local download directory if it does not exist.
        - If you see HTTP errors, check your access token and file permissions.
        - Retries up to 3 times on transient errors (see @retry).
    """
    access_token = get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    download_url = item['@microsoft.graph.downloadUrl']
    local_path = os.path.join(LOCAL_DOWNLOAD_DIR, item['name'])
    if not os.path.exists(LOCAL_DOWNLOAD_DIR):
        os.makedirs(LOCAL_DOWNLOAD_DIR)
    resp = requests.get(download_url, headers=headers)
    with open(local_path, 'wb') as f:
        f.write(resp.content)
    logging.info(f"Downloaded {item['name']} to {local_path}")
    return local_path


def move_image(image_path: str, processed_folder: str) -> str:
    """
    Move a processed image to the processed folder, appending a timestamp to the filename.

    Args:
        image_path (str): Path to the image file to move.
        processed_folder (str): Directory to move the image into.

    Returns:
        str: New path of the moved image file.

    Developer hints:
        - Creates the processed folder if it does not exist.
        - Appends a timestamp to avoid filename collisions.
        - If you see permission errors, check the destination directory permissions.
    """
    if not os.path.exists(processed_folder):
        os.makedirs(processed_folder)
    base = os.path.basename(image_path)
    name, ext = os.path.splitext(base)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    new_name = f"{name}_{timestamp}{ext}"
    dest = os.path.join(processed_folder, new_name)
    shutil.move(image_path, dest)
    logging.info(f"Moved {image_path} to {dest}")
    return dest
