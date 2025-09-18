
"""
onedrive_auth.py: Handles OneDrive OAuth2 authentication and token management for Susi.

Features:
    - Generates the authorization URL for Microsoft Graph API OAuth2 login/consent.
    - Exchanges authorization codes for access tokens and stores them locally.
    - Retrieves and refreshes stored tokens for Microsoft Graph API access.
    - Uses MSAL for OAuth2 and stores tokens in local files for reuse.

Developer hints:
    - Requires all OneDrive OAuth2 credentials in environment variables (see .env).
    - If you see token errors, check your credentials, token files, and MSAL version.
    - Use the __main__ block to run the OAuth2 flow interactively.

Error/warning message hints:
    - If you see 'No token found', run the OAuth2 flow to obtain a new token.
    - If you see 'Failed to refresh token', your refresh token may be expired or revoked.
    - Always log or print the full error message for troubleshooting.
"""


import os
import msal
import requests
import json
from typing import Optional
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()


CLIENT_ID = os.getenv("ONEDRIVE_APPLICATION_ID")
CLIENT_SECRET = os.getenv("ONEDRIVE_CLIENT_SECRET")
TENANT_ID = os.getenv("ONEDRIVE_DIRECTORY_ID")
REDIRECT_URI = os.getenv("ONEDRIVE_OAUTH_REDIRECT_URI")
AUTH_URL = os.getenv("ONEDRIVE_AUTHORIZATION_URL")
TOKEN_URL = os.getenv("ONEDRIVE_ACCESS_TOKEN_URL")
AUTH_SCOPES = ["Files.ReadWrite.All", "offline_access"]  # for auth URL
TOKEN_SCOPES = ["Files.ReadWrite.All"]  # for token request

TOKEN_CACHE_FILE = "token_cache.bin"
TOKEN_RESULT_FILE = "token_result.json"


def get_msal_app():
    """
    Create and return a MSAL ConfidentialClientApplication for OAuth2 flows.

    Returns:
        msal.ConfidentialClientApplication: The MSAL app instance.

    Developer hint:
        - Used internally for all token operations. No need to call directly.
    """
    return msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        client_credential=CLIENT_SECRET,
        token_cache=None
    )


def get_auth_url() -> str:
    """
    Generate the OneDrive OAuth2 authorization URL for user login and consent.

    Returns:
        str: The URL to direct the user for OAuth2 authorization.

    Developer hint:
        - Use this to start the OAuth2 flow in a browser.
        - If you see redirect or consent errors, check your Azure app registration.
    """
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "response_mode": "query",
        "scope": " ".join(AUTH_SCOPES),
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def get_token_from_code(auth_code: str) -> str:
    """
    Exchange an authorization code for an access token and save it locally.

    Args:
        auth_code (str): The authorization code returned from the OAuth2 flow.

    Returns:
        str: The access token.

    Raises:
        Exception: If the token exchange fails.

    Developer hint:
        - Saves both the access token and the full token result for refresh support.
        - If you see errors, check your client secret, redirect URI, and scopes.
    """
    app = get_msal_app()
    result = app.acquire_token_by_authorization_code(
        auth_code,
        scopes=TOKEN_SCOPES,
        redirect_uri=REDIRECT_URI
    )
    if "access_token" in result:
        # Save the full token result as JSON for refresh support
        with open(TOKEN_RESULT_FILE, "w") as f:
            json.dump(result, f)
        with open(TOKEN_CACHE_FILE, "w") as f:
            f.write(result["access_token"])
        return result["access_token"]
    else:
        raise Exception(f"Token error: {result}")


def get_access_token() -> Optional[str]:
    """
    Retrieve the stored OneDrive access token from the local cache file.

    Returns:
        Optional[str]: The access token if present, otherwise None.

    Developer hint:
        - Automatically refreshes the token if expired (if refresh_token is available).
        - If you see 'No token found', run the OAuth2 flow to obtain a new token.
        - If you see 'Failed to refresh token', your refresh token may be expired or revoked.
    """
    import time
    # Try to load the full token result (preferred)
    if os.path.exists(TOKEN_RESULT_FILE):
        with open(TOKEN_RESULT_FILE, "r") as f:
            token_result = json.load(f)
        access_token = token_result.get("access_token")
        expires_at = token_result.get("expires_at")
        refresh_token = token_result.get("refresh_token")
        # If token is expired or about to expire, refresh it
        if not expires_at or time.time() > expires_at - 60:
            # Try to refresh
            app = get_msal_app()
            result = app.acquire_token_by_refresh_token(
                refresh_token,
                scopes=TOKEN_SCOPES
            )
            if "access_token" in result:
                # Save new token result
                with open(TOKEN_RESULT_FILE, "w") as f:
                    json.dump(result, f)
                with open(TOKEN_CACHE_FILE, "w") as f:
                    f.write(result["access_token"])
                return result["access_token"]
            else:
                print("Failed to refresh token. Please run the OAuth flow again.")
                return None
        else:
            return access_token
    # Fallback: try old cache file
    elif os.path.exists(TOKEN_CACHE_FILE):
        with open(TOKEN_CACHE_FILE, "r") as f:
            return f.read().strip()
    else:
        print("No token found. Please run the OAuth flow.")
        return None


if __name__ == "__main__":
    """
    Run the OAuth2 flow interactively to obtain and save a OneDrive access token.

    Developer hint:
        - Run this script directly to start the OAuth2 flow and save a new token.
        - Follow the printed URL, authorize the app, and paste the code to complete authentication.
    """
    print("Go to the following URL and authorize the app:")
    print(get_auth_url())
    code = input("Paste the authorization code here: ")
    token = get_token_from_code(code)
    print("Access token saved.")
