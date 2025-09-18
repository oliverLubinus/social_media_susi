
"""
genai_api.py: Integration for a local LLM (DeepSeek) to generate LinkedIn and Instagram posts from news and context.

Features:
    - Uses a local LLM API (DeepSeek) to generate social media posts for LinkedIn and Instagram.
    - Accepts topic/content, target group, and a list of news articles as input.
    - Returns only the generated post text, never explanations or system messages.

Developer hints:
    - Requires LOCAL_GENAI_API_URL in environment variables (see .env).
    - If you see connection errors, check that the local LLM API is running and accessible.
    - If you see unexpected model output, check the system prompt and payload structure.
    - Use descriptive error messages when raising exceptions for easier debugging.

Error/warning message hints:
    - If you see a RuntimeError about LOCAL_GENAI_API_URL, check your environment variables.
    - If you see a requests.exceptions.RequestException, check the LLM server logs and network connectivity.
    - If the model returns no usable content, log the full response for troubleshooting.
"""

from typing import Optional, List, Dict
import requests
from .config import GENAI_API_URL, SYSTEM_PROMPT, LINKEDIN_SYSTEM_PROMPT

def generate_linkedin_post(content: str, target_group: Optional[str], news_articles: List[Dict]) -> str:
    """
    Use the local LLM to generate a LinkedIn post for the given topic/content, target group, and news articles.

    Args:
        content (str): The main topic or subject for the post.
        target_group (Optional[str]): The intended audience for the post.
        news_articles (List[Dict]): List of news articles (dicts with 'title' and 'description').

    Returns:
        str: The generated LinkedIn post text.

    Raises:
        RuntimeError: If the LOCAL_GENAI_API_URL environment variable is not set.
        requests.RequestException: If the LLM API call fails.

    Developer hint:
        - If the model output contains <think> or reasoning, only the post after </think> is returned.
        - If you see a requests error, check the LLM server logs and network.
        - If the model returns no usable content, log the full response for debugging.
    """
    if not GENAI_API_URL:
        raise RuntimeError("LOCAL_GENAI_API_URL environment variable not set.")
    # Prepare news summary for the prompt
    if news_articles:
        news_summary = "\n".join(f"- {a['title']}: {a.get('description','')[:200]}" for a in news_articles if 'title' in a)
    else:
        news_summary = "No recent news articles found."
    # Build the user prompt for the LLM
    user_prompt = (
        f"Topic: {content}\n"
        f"Target Group: {target_group or ''}\n"
        f"Relevant News:\n{news_summary}\n"
        "\nWrite a LinkedIn post for this context."
    )
    payload = {
        "model": "deepseek/deepseek-r1-0528-qwen3-8b",
        "messages": [
            {"role": "system", "content": LINKEDIN_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 900,
        "temperature": 0.8
    }
    # Call the local LLM API
    resp = requests.post(GENAI_API_URL, json=payload, timeout=180)
    resp.raise_for_status()
    data = resp.json()
    # Try OpenAI-compatible response structure
    if "choices" in data and data["choices"]:
        content = data["choices"][0]["message"]["content"].strip()
        # If the model outputs a <think> or reasoning section, extract only the actual post
        if "</think>" in content:
            post = content.split("</think>", 1)[-1].strip()
            if post:
                return post
        return content
    # Fallback: try 'result' or 'text' keys
    return data.get("result") or data.get("text") or "[No response from model]"


def generate_instagram_post(content: str, target_group: Optional[str], news_articles: List[Dict]) -> str:
    """
    Use the local LLM to generate an Instagram post for the given topic/content, target group, and news articles.

    Args:
        content (str): The main topic or subject for the post.
        target_group (Optional[str]): The intended audience for the post.
        news_articles (List[Dict]): List of news articles (dicts with 'title' and 'description').

    Returns:
        str: The generated Instagram post text.

    Raises:
        RuntimeError: If the LOCAL_GENAI_API_URL environment variable is not set.
        requests.RequestException: If the LLM API call fails.

    Developer hint:
        - If the model output contains <think> or reasoning, only the post after </think> is returned.
        - If you see a requests error, check the LLM server logs and network.
        - If the model returns no usable content, log the full response for debugging.
    """
    if not GENAI_API_URL:
        raise RuntimeError("LOCAL_GENAI_API_URL environment variable not set.")
    # Prepare news summary for the prompt
    if news_articles:
        news_summary = "\n".join(f"- {a['title']}: {a.get('description','')[:200]}" for a in news_articles if 'title' in a)
    else:
        news_summary = "No recent news articles found."
    # Build the user prompt for the LLM
    user_prompt = (
        f"Topic: {content}\n"
        f"Target Group: {target_group or ''}\n"
        f"Relevant News:\n{news_summary}\n"
        "\nWrite an Instagram post for this context."
    )
    payload = {
        "model": "deepseek/deepseek-r1-0528-qwen3-8b",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 600,
        "temperature": 0.8
    }
    # Call the local LLM API
    resp = requests.post(GENAI_API_URL, json=payload, timeout=180)
    resp.raise_for_status()
    data = resp.json()
    # Try OpenAI-compatible response structure
    if "choices" in data and data["choices"]:
        content = data["choices"][0]["message"]["content"].strip()
        # If the model outputs a <think> or reasoning section, extract only the actual post
        if "</think>" in content:
            # Use the part after </think>
            post = content.split("</think>", 1)[-1].strip()
            if post:
                return post
        return content
    # Fallback: try 'result' or 'text' keys
    return data.get("result") or data.get("text") or "[No response from model]"
