"""
Email utilities for Susi: sending emails via Gmail API (OAuth2) or SMTP, with robust retry and logging.

Developer hints:
    - Use send_error_email() for error notifications; it will use Gmail API if configured, otherwise fallback to SMTP.
    - All email sending is retried up to 3 times with exponential backoff.
    - Check logs for detailed error messages and troubleshooting hints.
"""
import os
import base64
import smtplib
import logging
from email.mime.text import MIMEText
from typing import Any, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log

# Gmail API imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_gmail_service(config: Optional[Dict] = None) -> Any:
    """
    Authenticate and return a Gmail API service client using OAuth2 credentials.

    Args:
        config (dict, optional): Email config. Uses env vars or defaults if not provided.

    Returns:
        googleapiclient.discovery.Resource: Gmail API service client.

    Developer hint:
        - Requires valid client_secret.json and gmail_token.json files.
        - If token is expired or missing, will prompt for OAuth flow in browser.
        - Set GMAIL_CLIENT_SECRET_FILE and GMAIL_TOKEN_FILE in env or config for custom paths.
    """
    # Load credential file paths from env, config, or defaults
    client_secret_file = os.getenv("GMAIL_CLIENT_SECRET_FILE")
    token_file = os.getenv("GMAIL_TOKEN_FILE")
    if config:
        client_secret_file = client_secret_file or config['email'].get('client_secret_file', 'client_secret.json')
        token_file = token_file or config['email'].get('token_file', 'gmail_token.json')
    else:
        client_secret_file = client_secret_file or 'client_secret.json'
        token_file = token_file or 'gmail_token.json'

    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
    service = build('gmail', 'v1', credentials=creds)
    return service

def send_gmail(subject: str, body: str, config: Dict) -> str:
    """
    Send an email using the Gmail API.

    Args:
        subject (str): Subject line of the email.
        body (str): Body text of the email.
        config (dict): Email configuration, must include recipient and username.

    Returns:
        str: The Gmail message ID of the sent email.

    Raises:
        Exception: If sending fails (will be retried by caller).

    Developer hint:
        - Make sure Gmail API is enabled and OAuth credentials are valid.
        - Check logs for API errors (e.g., invalid token, quota exceeded).
    """
    service = get_gmail_service(config)
    message = MIMEText(body)
    message['to'] = config['email']['recipient']
    message['from'] = config['email']['username']
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    message_body = {'raw': raw}
    sent = service.users().messages().send(userId='me', body=message_body).execute()
    return sent.get('id')

    # Compose and send the email using Gmail API

# Retry config: 3 attempts, exponential backoff, log before each retry
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    before_sleep=before_sleep_log(logging.getLogger("email_utils"), logging.WARNING),
    reraise=True
)
def _send_error_email_with_retry(subject: str, body: str, config: Dict) -> None:
    """
    Internal: Send an error email using Gmail API or fallback to SMTP, with retry and logging.

    Args:
        subject (str): Email subject.
        body (str): Email body.
        config (dict): Email config.

    Raises:
        Exception: If all attempts fail.

    Developer hint:
        - Will try Gmail API first if provider is 'gmail', then fallback to SMTP.
        - All errors are logged with hints for troubleshooting (e.g., check credentials, network, API status).
    """
    provider = config['email'].get('provider', '').lower()
    if provider == 'gmail':
        try:
            send_gmail(subject, body, config)
            logging.info("Error email sent via Gmail API.")
            return
        except Exception as e:
            # Error hint: Check Gmail API credentials, token, and quota.
            logging.error(f"Failed to send error email via Gmail API: {e}")
            # fallback to SMTP below
    # fallback: SMTP
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = config['email']['username']
    msg['To'] = config['email']['recipient']
    try:
        with smtplib.SMTP(config['email']['smtp_server'], config['email']['smtp_port']) as server:
            server.starttls()
            server.login(config['email']['username'], config['email']['password'])
            server.send_message(msg)
        logging.info("Error email sent via SMTP.")
    except Exception as e:
        # Error hint: Check SMTP server, port, username, password, and network connection.
        logging.error(f"Failed to send error email via SMTP: {e}")
        raise

def send_error_email(subject: str, body: str, config: Dict) -> None:
    """
    Send an error notification email using Gmail API (OAuth) if provider is gmail, otherwise fallback to SMTP.
    Retries up to 3 times on failure, with exponential backoff and logging.

    Args:
        subject (str): Email subject.
        body (str): Email body.
        config (dict): Email config.

    Developer hint:
        - Use this function for all error notifications in Susi.
        - Check logs for detailed error messages and troubleshooting hints if email fails.
    """
    try:
        _send_error_email_with_retry(subject, body, config)
    except Exception as e:
        # Error hint: All attempts failed. Check previous log messages for root cause.
        logging.error(f"All attempts to send error email failed: {e}")