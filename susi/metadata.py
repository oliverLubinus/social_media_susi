
"""
metadata.py: Extracts metadata (title, comment, etc.) from image files for Susi workflows.

Features:
    - Extracts EXIF metadata (title, comment) from images using exifread.
    - Handles Windows-specific XPComment decoding.
    - Can be extended for IPTC/XMP metadata using PIL or other libraries.

Developer hints:
    - If you see missing metadata, check the image file for EXIF tags using an external tool.
    - For IPTC/XMP support, extend this module with PIL or other libraries.
    - Handles most common EXIF fields; customize as needed for your workflow.

Error/warning message hints:
    - If you see decode errors for XPComment, the field may not be UTF-16LE or may be missing.
    - If you see empty fields, check the image's metadata with exiftool or similar.
"""

import os
import exifread
from PIL import Image
from typing import Dict

def extract_metadata(image_path: str) -> Dict[str, str]:
    """
    Extract title, comment, and other metadata from an image file using EXIF tags.

    Args:
        image_path (str): Path to the image file.

    Returns:
        dict: Dictionary containing extracted metadata fields (e.g., 'title', 'comment').

    Developer hint:
        - Uses exifread for EXIF tags. Optionally extend for IPTC/XMP with PIL or other libraries.
        - Handles XPComment decoding for Windows-written metadata.
        - If you see missing or garbled fields, check the image with exiftool or similar.
    """
    metadata = {}
    with open(image_path, 'rb') as f:
        tags = exifread.process_file(f, details=False)
        # Extract title from EXIF (ImageDescription)
        title = tags.get('Image ImageDescription', '')
        if hasattr(title, 'printable'):
            title = title.printable
        metadata['title'] = title
        # Extract comment (XPComment is often a byte array on Windows)
        comment = tags.get('Image XPComment', '')
        if hasattr(comment, 'values') and isinstance(comment.values, list):
            try:
                comment_bytes = bytes(comment.values)
                comment_str = comment_bytes.decode('utf-16le').rstrip('\x00')
                metadata['comment'] = comment_str
            except Exception:
                # Error hint: XPComment may not be UTF-16LE or may be missing.
                metadata['comment'] = str(comment)
        elif hasattr(comment, 'printable'):
            metadata['comment'] = comment.printable
        else:
            metadata['comment'] = str(comment)
    # Optionally, use PIL for IPTC/XMP metadata extraction here
    return metadata
