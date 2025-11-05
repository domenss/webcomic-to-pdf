"""Utility functions for the webcomic2pdf project."""

import re


def sanitize_filename(name: str) -> str:
    """Remove invalid characters from filename.
    
    Args:
        name: The filename to sanitize
        
    Returns:
        Sanitized filename safe for filesystem use
    """
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    return re.sub(invalid_chars, '_', name).strip('. ')
