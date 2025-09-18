
"""
Excel monitor for Susi: Reads and updates rows in a OneDrive Excel file for workflow automation.

Features:
    - Reads the worksheet 'posts' in the file '/Documents/SocialMedia/SocialMediaSusi/posts/posts.xlsx'.
    - Returns rows where the 'processed' column is empty.
    - Marks rows as processed by writing 'x' in the 'processed' column after successful processing.
    - Writes generated posts to the 'Instagram' and 'LinkedIn' columns.

Developer hints:
    - Requires Microsoft Graph API authentication (see susi/onedrive_auth.py).
    - All API calls use the current access token; check logs for token or permission errors.
    - If you see column not found errors, check your Excel sheet headers.
"""

import os
import requests
from typing import List, Dict, Any
from susi.onedrive_auth import get_access_token


# Configuration from environment variables
EXCEL_PATH = os.getenv("ONEDRIVE_POSTS_EXCEL_PATH", "/Documents/SocialMedia/SocialMediaSusi/posts/posts.xlsx")
SHEET_NAME = os.getenv("ONEDRIVE_POSTS_EXCEL_SHEET_NAME", "posts")
GRAPH_ROOT = os.getenv("ONEDRIVE_GRAPH_ROOT", "https://graph.microsoft.com/v1.0/me/drive/root:")


def get_excel_rows() -> List[Dict[str, Any]]:
    """
    Fetch all rows from the 'posts' worksheet in the Excel file on OneDrive.

    Returns:
        List[dict]: List of row dicts (column name to value) for unprocessed rows.

    Developer hint:
        - Only rows where the 'processed' column is empty are returned.
        - If you see an API error, check your access token and permissions.
        - If you see missing columns, check your Excel sheet header.
    """
    # Get access token and set headers for Microsoft Graph API
    access_token = get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    # Get used range (all rows/columns with data)
    url = f"{GRAPH_ROOT}{EXCEL_PATH}:/workbook/worksheets('{SHEET_NAME}')/usedRange?valuesOnly=true"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    values = resp.json()["values"]
    if not values or len(values) < 2:
        # Warning: No data found in the worksheet.
        return []
    header = values[0]
    rows = [dict(zip(header, row)) for row in values[1:]]
    # Only return rows not yet processed (processed column is empty)
    return [row for row in rows if not row.get("processed")]
def write_linkedin_post(row_index: int, post_text: str) -> None:
    """
    Write the generated LinkedIn post to the 'LinkedIn' column in the given row.

    Args:
        row_index (int): 0-based row index (excluding header), as returned by get_excel_rows().
        post_text (str): The LinkedIn post text to write.

    Raises:
        Exception: If the 'LinkedIn' column is not found or the API call fails.

    Developer hint:
        - If you see a ValueError, check that your Excel sheet has a 'LinkedIn' column in the header row.
        - If you see an API error, check your access token and permissions.
    """
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    # Find the LinkedIn column index in the header row
    url = f"{GRAPH_ROOT}{EXCEL_PATH}:/workbook/worksheets('{SHEET_NAME}')/usedRange?valuesOnly=true"
    resp = requests.get(url, headers={"Authorization": f"Bearer {access_token}"})
    resp.raise_for_status()
    values = resp.json()["values"]
    header = values[0]
    try:
        linkedin_col = header.index("LinkedIn")
    except ValueError:
        # Error hint: Check your Excel sheet header for a 'LinkedIn' column.
        raise Exception("No 'LinkedIn' column found in sheet header.")
    # The row to update (add 1 for header row)
    excel_row = row_index + 1
    cell_address = f"{chr(65+linkedin_col)}{excel_row+1}"  # e.g., F2
    patch_url = f"{GRAPH_ROOT}{EXCEL_PATH}:/workbook/worksheets('{SHEET_NAME}')/range(address='{cell_address}')"
    data = {"values": [[post_text]]}
    patch_resp = requests.patch(patch_url, headers=headers, json=data)
    patch_resp.raise_for_status()

def write_instagram_post(row_index: int, post_text: str) -> None:
    """
    Write the generated Instagram post to the 'Instagram' column in the given row.

    Args:
        row_index (int): 0-based row index (excluding header), as returned by get_excel_rows().
        post_text (str): The Instagram post text to write.

    Raises:
        Exception: If the 'Instagram' column is not found or the API call fails.

    Developer hint:
        - If you see a ValueError, check that your Excel sheet has an 'Instagram' column in the header row.
        - If you see an API error, check your access token and permissions.
    """
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    # Find the Instagram column index in the header row
    url = f"{GRAPH_ROOT}{EXCEL_PATH}:/workbook/worksheets('{SHEET_NAME}')/usedRange?valuesOnly=true"
    resp = requests.get(url, headers={"Authorization": f"Bearer {access_token}"})
    resp.raise_for_status()
    values = resp.json()["values"]
    header = values[0]
    try:
        insta_col = header.index("Instagram")
    except ValueError:
        # Error hint: Check your Excel sheet header for an 'Instagram' column.
        raise Exception("No 'Instagram' column found in sheet header.")
    # The row to update (add 1 for header row)
    excel_row = row_index + 1
    cell_address = f"{chr(65+insta_col)}{excel_row+1}"  # e.g., E2
    patch_url = f"{GRAPH_ROOT}{EXCEL_PATH}:/workbook/worksheets('{SHEET_NAME}')/range(address='{cell_address}')"
    data = {"values": [[post_text]]}
    patch_resp = requests.patch(patch_url, headers=headers, json=data)
    patch_resp.raise_for_status()
def mark_row_processed(row_index: int) -> None:
    """
    Mark a row as processed by writing 'x' in the 'processed' column.

    Args:
        row_index (int): 0-based row index (excluding header), as returned by get_excel_rows().

    Raises:
        Exception: If the 'processed' column is not found or the API call fails.

    Developer hint:
        - If you see a ValueError, check that your Excel sheet has a 'processed' column in the header row.
        - If you see an API error, check your access token and permissions.
    """
    # Get access token and set headers for Microsoft Graph API
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    # Find the processed column index in the header row
    url = f"{GRAPH_ROOT}{EXCEL_PATH}:/workbook/worksheets('{SHEET_NAME}')/usedRange?valuesOnly=true"
    resp = requests.get(url, headers={"Authorization": f"Bearer {access_token}"})
    resp.raise_for_status()
    values = resp.json()["values"]
    header = values[0]
    try:
        processed_col = header.index("processed")
    except ValueError:
        # Error hint: Check your Excel sheet header for a 'processed' column.
        raise Exception("No 'processed' column found in sheet header.")
    # The row to update (add 1 for header row)
    excel_row = row_index + 1
    cell_address = f"{chr(65+processed_col)}{excel_row+1}"  # e.g., D2
    patch_url = f"{GRAPH_ROOT}{EXCEL_PATH}:/workbook/worksheets('{SHEET_NAME}')/range(address='{cell_address}')"
    data = {"values": [["x"]]}
    patch_resp = requests.patch(patch_url, headers=headers, json=data)
    patch_resp.raise_for_status()

