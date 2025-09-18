"""
news_api.py: Fetches news articles for a given topic and (optionally) target group using NewsAPI.org.

Features:
    - Fetches relevant news articles for a topic and/or target group using NewsAPI.org.
    - Returns a list of article dicts (title, url, description, etc.).

Developer hints:
    - Requires NEWSAPI_KEY in environment variables (see .env).
    - If you see API errors, check your API key, query, and NewsAPI.org status.
    - Use max_results to control the number of articles returned.

Error/warning message hints:
    - If you see a RuntimeError about NEWSAPI_KEY, check your environment variables.
    - If you see requests.exceptions.RequestException, check your network and NewsAPI.org status.
    - If you get empty results, try a broader query or check NewsAPI.org limits.
"""

import os
import requests
from typing import List, Dict, Optional

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"


def fetch_news_articles(query: str, target_group: Optional[str] = None, max_results: int = 5) -> List[Dict]:
    """
    Fetch news articles from NewsAPI.org for a given query and optional target group.

    Args:
        query (str): Main topic or search query.
        target_group (Optional[str]): Optional target group to refine the search.
        max_results (int): Maximum number of articles to return (default: 5).

    Returns:
        List[dict]: List of article dicts (title, url, description, etc.).

    Raises:
        RuntimeError: If NEWSAPI_KEY is not set.
        requests.RequestException: If the API call fails.

    Developer hint:
        - If you get empty results, try a broader query or check NewsAPI.org limits.
        - Log the full API response for troubleshooting if needed.
    """
    if not NEWSAPI_KEY:
        raise RuntimeError("NEWSAPI_KEY environment variable not set.")
    # Build the query string
    q = query
    if target_group:
        q += f" {target_group}"
    params = {
        "q": q,
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": max_results,
        "apiKey": NEWSAPI_KEY
    }
    # Call NewsAPI.org
    resp = requests.get(NEWSAPI_ENDPOINT, params=params)
    resp.raise_for_status()
    data = resp.json()
    # Return the list of articles (may be empty)
    return data.get("articles", [])
