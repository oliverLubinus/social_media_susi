
"""
main.py: Main workflow and orchestration for the Susi social media agent.

Features:
    - Loads configuration and environment variables using centralized helpers from config.py.
    - Sets up robust logging (file + console, rotation, structured format) via config.py utilities.
    - Orchestrates Excel-driven and image-driven workflows for social media posting.
    - Handles OneDrive, S3, Instagram, and email integration.
    - Provides robust error handling, retry logic, and notification.

Developer hints:
    - All config values are loaded and type-checked via get_config() in config.py.
    - Logging is configured using setup_logging() from config.py for consistency across modules.
    - Use the logger for all workflow steps and errors for traceability.
    - Helper functions for config/env var resolution are now centralized in config.py.

Error/warning message hints:
    - If you see 'Unknown trigger_mode', check your main() call and config.
    - If you see API or network errors, check credentials, tokens, and network connectivity.
    - If you see 'Failed to write' or 'Failed to generate', check the LLM, Excel, or API logs for details.
"""



from dotenv import load_dotenv
from .onedrive_auth import get_access_token
from .onedrive_monitor import list_onedrive_images, download_onedrive_image
from . import excel_monitor
from .metadata import extract_metadata
from .post_generator import generate_post_text
from .social_posters.instagram import InstagramPoster
from .email_utils import send_error_email, send_gmail
from .services.s3 import upload_file_to_s3
from .exceptions import S3UploadError, InstagramPostError
from .news_api import fetch_news_articles
from .genai_api import generate_instagram_post, generate_linkedin_post
import logging
import time
import traceback
import requests
import os
import schedule
from typing import Optional

# Import config constants
from .config import SCHEDULE_KEY, IMAGE_DAY_KEY, IMAGE_TIME_KEY, INSTAGRAM_DAY_KEY, INSTAGRAM_TIME_KEY, DAY_MAP

# Load environment variables from .env
load_dotenv()

# --- Config and logging setup ---
from .config import get_config, setup_logging

config = get_config()
logger = setup_logging(config)

# helpers
def keep_onedrive_token_alive():
    """
    Ensures the OneDrive access token is refreshed if needed.

    Developer hint:
        - Call this before any OneDrive API operation to avoid token expiry.
        - If you see a warning, re-authentication may be required.
    """
    token = get_access_token()
    if token:
        logging.info("OneDrive access token keep-alive: token is valid or refreshed.")
    else:
        logging.warning("OneDrive access token keep-alive: failed to refresh token. Re-authentication may be required.")

def process_excel_topics(poster=None, dry_run=False) -> None:
    """
    Process new topics from the Excel file: fetch unprocessed rows, extract content and target group, fetch news, generate posts, and write results.

    Args:
        poster: SocialPoster instance (default: InstagramPoster).
        dry_run (bool): If True, do not actually post (for testing).

    Developer hint:
        - This is the main entry for Excel-driven workflow automation.
        - All errors are logged and trigger error notification emails.
        - If you see workflow aborts, check the logs for which step failed.
    """
    logger.info("Starting Excel-driven topic processing.")
    rows = excel_monitor.get_excel_rows()
    if not rows:
        logger.info("No new topics found in Excel file.")
        return
    if poster is None:
        poster = InstagramPoster()
    for idx, row in enumerate(rows):
        logger.debug(f"Processing Excel row {idx}: {row}")
        try:
            content = row.get('Content') or row.get('content')
            target_group = row.get('Target Group') or row.get('target group') or row.get('target_group')
            if not content:
                logger.warning(f"Row {idx} missing 'content' column, skipping.")
                continue
            logger.info(f"Processing Excel row {idx}: content='{content}', target_group='{target_group}'")
            # Fetch news articles relevant to content and target_group
            try:
                news_articles = fetch_news_articles(content, target_group)
                logger.info(f"Fetched {len(news_articles)} news articles for content '{content}'.")
            except Exception as e:
                logger.exception(f"Failed to fetch news articles for content '{content}': {e}")
                news_articles = []
                send_error(
                    subject="Susi Excel Workflow: News Fetch Failed",
                    body=f"Failed to fetch news articles for content '{content}', target group '{target_group}'.\nError: {e}",
                    config=config
                )
            # Generate a post using the local LLM
            try:
                caption = generate_instagram_post(content, target_group, news_articles)
                logger.info(f"Generated Instagram post for row {idx}.")
            except Exception as e:
                logger.exception(f"Failed to generate Instagram post for content '{content}': {e}")
                send_error(
                    subject="Susi Excel Workflow: Instagram Post Generation Failed",
                    body=f"Failed to generate Instagram post for content '{content}', target group '{target_group}'.\nError: {e}",
                    config=config
                )
                # Fallback: use news article titles if LLM fails
                if news_articles:
                    article_titles = '\n'.join(f"- {a['title']}" for a in news_articles if 'title' in a)
                    caption = f"Topic: {content}\nTarget Group: {target_group}\n\nRelevant News:\n{article_titles}"
                else:
                    caption = f"Topic: {content}\nTarget Group: {target_group}\n(No relevant news articles found)"
            # Write the generated Instagram post to the 'Instagram' column in the same row
            try:
                excel_monitor.write_instagram_post(idx, caption)
                logger.info(f"Wrote Instagram post to Excel for row {idx}.")
            except Exception as e:
                logger.exception(f"Failed to write Instagram post to Excel for row {idx}: {e}")
                send_error(
                    subject="Susi Excel Workflow: Instagram Post Write Failed",
                    body=f"Failed to write Instagram post to Excel for row {idx}, content '{content}'.\nError: {e}",
                    config=config
                )

            # Generate and write LinkedIn post
            linkedin_success = False
            try:
                linkedin_post = generate_linkedin_post(content, target_group, news_articles)
                logger.info(f"Generated LinkedIn post for row {idx}.")
            except Exception as e:
                logger.exception(f"Failed to generate LinkedIn post for row {idx}: {e}")
                send_error(
                    subject="Susi Excel Workflow: LinkedIn Post Generation Failed",
                    body=f"Failed to generate LinkedIn post for content '{content}', target group '{target_group}'.\nError: {e}",
                    config=config
                )
                linkedin_post = None
            if linkedin_post:
                try:
                    excel_monitor.write_linkedin_post(idx, linkedin_post)
                    linkedin_success = True
                    logger.info(f"Wrote LinkedIn post to Excel for row {idx}.")
                except Exception as e:
                    logger.exception(f"Failed to write LinkedIn post to Excel for row {idx}: {e}")
                    send_error(
                        subject="Susi Excel Workflow: LinkedIn Post Write Failed",
                        body=f"Failed to write LinkedIn post to Excel for row {idx}, content '{content}'.\nError: {e}",
                        config=config
                    )

            # Mark as processed only if both Instagram and LinkedIn posts were written
            if caption and linkedin_success:
                excel_monitor.mark_row_processed(idx)
                logger.info(f"Processed and marked Excel row {idx} for content '{content}'.")
                send_confirmation(
                    subject="Susi Excel Workflow: Both Posts Created",
                    body=f"Successfully created and stored Instagram and LinkedIn posts for content: '{content}', target group: '{target_group}'.",
                    config=config
                )
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Error processing Excel row {idx}: {e}\n{tb}")
            send_error(
                subject="Susi Excel Workflow: Unexpected Error",
                body=f"Unexpected error processing Excel row {idx}, content '{content}'.\nError: {e}\n\nTraceback:\n{tb}",
                config=config
            )

def move_onedrive_file_to_processed(item: dict, config: dict) -> None:
    """
    Move a file in OneDrive to the processed folder using Microsoft Graph API.

    Args:
        item (dict): The OneDrive file item dict.
        config (dict): The loaded configuration dict.

    Developer hint:
        - If you see a failure, check OneDrive API permissions and folder paths.
        - Always log the full API response for troubleshooting.
    """

    logging.info(f"Moving file '{item['name']}' (ID: {item['id']}) to processed folder in OneDrive.")
    access_token = __import__('susi.onedrive_auth', fromlist=['get_access_token']).get_access_token()
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    processed_folder = config['onedrive']['processed_folder']
    new_path = processed_folder.rstrip('/') + '/' + item['name']
    url = f"https://graph.microsoft.com/v1.0/me/drive/items/{item['id']}"
    data = {"parentReference": {"path": f"/drive/root:{processed_folder}"}}
    resp = requests.patch(url, headers=headers, json=data)
    if resp.status_code in (200, 201):
        logging.info(f"Moved '{item['name']}' to '{processed_folder}' in OneDrive.")
    else:
        logging.error(f"Failed to move '{item['name']}' to '{processed_folder}': {resp.text}")

def process_images(images: Optional[list] = None, seen_ids: Optional[set] = None, poster=None) -> None:
    """
    Process a list of images: download, extract metadata, generate caption, upload to S3, post to social platform, and notify.

    Args:
        images (list): List of image dicts (from OneDrive). If None, fetches from OneDrive.
        seen_ids (set): Set of already-processed image IDs (for polling mode).
        poster: SocialPoster instance (default: InstagramPoster).

    Developer hint:
        - This is the main entry for image-driven workflow automation.
        - All errors are logged and trigger error notification emails.
        - If you see repeated failures, check OneDrive, S3, and Instagram API credentials and logs.
    """
    keep_onedrive_token_alive()
    template = config['template']
    if images is None:
        logging.info("Fetching images from OneDrive...")
        images = list_onedrive_images()
    if seen_ids is not None:
        images = [img for img in images if img['id'] not in seen_ids]
    if not images:
        logging.info("No new images found in OneDrive.")
        return
    if poster is None:
        poster = InstagramPoster()
    for item in images:
        try:
            logging.info(f"Processing image: {item['name']} (ID: {item['id']})")
            try:
                local_path = download_onedrive_image(item)
            except Exception as e:
                tb = traceback.format_exc()
                logging.error(f"OneDrive download failed for {item['name']}: {e}\n{tb}")
                send_error(
                    subject="Susi OneDrive Download Failed",
                    body=f"Failed to download {item['name']} from OneDrive.\nError: {e}\n\nTraceback:\n{tb}",
                    config=config
                )
                continue
            logging.info(f"Downloaded image to {local_path}")
            try:
                metadata = extract_metadata(local_path)
                logging.debug(f"Extracted metadata: {metadata}")
                caption = generate_post_text(metadata, template)
                logging.debug(f"Generated caption: {caption}")
            except Exception as e:
                tb = traceback.format_exc()
                logging.error(f"Metadata extraction or caption generation failed for {item['name']}: {e}\n{tb}")
                send_error(
                    subject="Susi Metadata/Caption Error",
                    body=f"Failed to extract metadata or generate caption for {item['name']}.\nError: {e}\n\nTraceback:\n{tb}",
                    config=config
                )
                continue

            aws_cfg = config['aws']
            logging.info(f"Uploading {local_path} to S3 bucket '{aws_cfg['s3_bucket']}'...")
            try:
                s3_url = upload_file_to_s3(
                    file_path=local_path,
                    bucket_name=aws_cfg['s3_bucket'],
                    object_name=None,
                    aws_access_key_id=aws_cfg.get('access_key_id'),
                    aws_secret_access_key=aws_cfg.get('secret_access_key'),
                    region_name=aws_cfg['region']
                )
                if not s3_url:
                    raise S3UploadError(f"upload_file_to_s3 returned None for {local_path}")
            except Exception as e:
                tb = traceback.format_exc()
                logging.error(f"S3 upload failed for {item['name']}: {e}\n{tb}")
                send_error(
                    subject="Susi S3 Upload Failed",
                    body=f"Failed to upload {local_path} to S3.\nError: {e}\n\nTraceback:\n{tb}",
                    config=config
                )
                continue
            logging.info(f"Uploaded to S3: {s3_url}")

            logging.info(f"Posting image to social platform: {s3_url}")
            try:
                success = poster.post(s3_url, caption, config)
                if not success:
                    raise InstagramPostError(f"poster.post returned False for {item['name']}")
            except Exception as e:
                tb = traceback.format_exc()
                logging.error(f"Social post failed for {item['name']}: {e}\n{tb}")
                send_error(
                    subject="Susi Social Post Failed",
                    body=f"Failed to post {s3_url} to social platform.\nError: {e}\n\nTraceback:\n{tb}",
                    config=config
                )
                continue
            logging.info(f"Successfully posted image to social platform: {item['name']}")
            move_onedrive_file_to_processed(item, config)
            os.remove(local_path)
            logging.info(f"Deleted local file: {local_path}")
            send_confirmation(
                subject="Susi Post Created",
                body=f"A post was successfully created for image: {item['name']}\n\nCaption:\n{caption}",
                config=config
            )
            if seen_ids is not None:
                seen_ids.add(item['id'])
        except Exception as e:
            tb = traceback.format_exc()
            logging.error(f"Unexpected error processing {item['name']}: {e}\n{tb}")
            send_error(
                subject="Susi Unexpected Error",
                body=f"Unexpected error processing {item['name']}: {e}\n\nTraceback:\n{tb}",
                config=config
            )

def send_confirmation(subject: str, body: str, config: dict) -> None:
    """
    Send a confirmation email after a successful post.

    Args:
        subject (str): Email subject.
        body (str): Email body.
        config (dict): The loaded configuration dict.

    Developer hint:
        - Uses Gmail API if configured, otherwise falls back to SMTP.
        - If you see email failures, check your email provider config and credentials.
    """
    provider = config['email'].get('provider', '').lower()
    if provider == 'gmail':
        try:
            send_gmail(subject, body, config)
            logging.info("Confirmation email sent via Gmail API.")
        except Exception as e:
            logging.error(f"Failed to send confirmation email via Gmail API: {e}")
    else:
        send_error_email(subject, body, config)

def send_error(subject: str, body: str, config: dict) -> None:
    """
    Send an error notification email.

    Args:
        subject (str): Email subject.
        body (str): Email body.
        config (dict): The loaded configuration dict.

    Developer hint:
        - Uses Gmail API if configured, otherwise falls back to SMTP.
        - If you see email failures, check your email provider config and credentials.
    """
    provider = config['email'].get('provider', '').lower()
    if provider == 'gmail':
        try:
            send_gmail(subject, body, config)
            logging.info("Error email sent via Gmail API.")
        except Exception as e:
            logging.error(f"Failed to send error email via Gmail API: {e}")
    else:
        send_error_email(subject, body, config)

def main(trigger_mode: str = "polling") -> None:
    """
    Main entry point for Susi. Runs in polling or schedule mode.

    Args:
        trigger_mode (str): "polling" (default) or "schedule".

    Developer hint:
        - In polling mode, processes new images and Excel topics every hour.
        - In schedule mode, uses the schedule config to run workflows at specific times.
        - If you see scheduling errors, check your config and the day/time values.
    """
    logging.info(f"Susi started with trigger mode: {trigger_mode}")
    if trigger_mode == "polling":
        seen_ids = set()
        poll_interval = 3600  # seconds (1 hour)
        while True:
            images = list_onedrive_images()
            process_images(images, seen_ids)
            # Process new Excel topics as well
            process_excel_topics()
            time.sleep(poll_interval)
    elif trigger_mode == "schedule":
        # Schedule image workflow on configured day/time
        img_day = config[SCHEDULE_KEY].get(IMAGE_DAY_KEY, 'Tuesday').lower()
        img_time = config[SCHEDULE_KEY].get(IMAGE_TIME_KEY, '09:00')
        # Schedule Instagram post (Excel workflow) on configured day/time
        post_day = config[SCHEDULE_KEY].get(INSTAGRAM_DAY_KEY, 'Thursday').lower()
        post_time = config[SCHEDULE_KEY].get(INSTAGRAM_TIME_KEY, '09:00')

        if img_day in DAY_MAP:
            DAY_MAP[img_day].at(img_time).do(process_images)
        else:
            logging.error(f"Unknown image workflow schedule day: {img_day}")
            raise ValueError(f"Unknown image workflow schedule day: {img_day}")
        if post_day in DAY_MAP:
            DAY_MAP[post_day].at(post_time).do(process_excel_topics)
        else:
            logging.error(f"Unknown Instagram workflow schedule day: {post_day}")
            raise ValueError(f"Unknown Instagram workflow schedule day: {post_day}")
        logging.info("Scheduler started.")
        while True:
            schedule.run_pending()
            time.sleep(30)
    else:
        logging.error(f"Unknown trigger_mode: {trigger_mode}")
        raise ValueError(f"Unknown trigger_mode: {trigger_mode}")

if __name__ == "__main__":
    # Set trigger_mode to "polling" or "schedule" as needed
    main(trigger_mode="schedule")
