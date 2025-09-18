
"""
post_generator.py: Utilities for generating social media post captions from image metadata and templates.

Features:
    - Generates formatted post captions using metadata and customizable templates.

Developer hints:
    - Template should use Python's str.format() syntax, e.g. "{title}: {comment}".
    - Metadata dict should contain keys matching template placeholders (e.g. 'title', 'comment').

Error/warning message hints:
    - If you see KeyError, check that all placeholders in the template are present in metadata.
    - If you see empty captions, check for missing or empty metadata fields.
"""

import os
import logging
from .metadata import extract_metadata
from typing import Dict

def generate_post_text(metadata: Dict[str, str], template: str) -> str:
    """
    Generate a post caption by formatting a template with image metadata.

    Args:
        metadata (dict): Dictionary containing 'title', 'comment', etc.
        template (str): Template string with placeholders for metadata fields.

    Returns:
        str: Formatted post caption.

    Example:
        template = "{title}: {comment}"

    Developer hints:
        - Template must use keys present in metadata (e.g. 'title', 'comment').
        - Add more fields to metadata/template as needed for richer captions.

    Error/warning message hints:
        - KeyError: Check that all template placeholders are present in metadata.
        - Empty caption: Check for missing or empty metadata fields.
    """
    # Clean up metadata for formatting
    title = metadata.get('title', '').strip()
    comment = metadata.get('comment', '').strip()
    # Replace linebreaks in comment with a single space
    comment = ' '.join(comment.split())
    return template.format(title=title, comment=comment)
