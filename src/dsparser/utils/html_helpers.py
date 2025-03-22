"""
Helper functions for working with Discord HTML files.
"""

import re
from typing import Tuple, Optional


def extract_html_header_footer(content: str) -> Tuple[str, str]:
    """
    Extracts the header and footer from HTML content.
    
    Args:
        content: HTML file content (beginning)
        
    Returns:
        Tuple (header, footer)
    """
    chatlog_div_start = content.find('<div class="chatlog">')
    if chatlog_div_start != -1:
        header = content[:chatlog_div_start]
    else:
        # If the specific div is not found, use a simple header
        header = "<!DOCTYPE html><html><head><title>Discord Messages</title><meta charset='utf-8'></head><body>"
    
    footer = "</div></body></html>"
    
    return header, footer


def parse_message_date(message_html: str) -> Optional[str]:
    """
    Extracts the year from Discord message HTML.
    
    Args:
        message_html: HTML code of the message
        
    Returns:
        String with the year or None if year not found
    """
    # Look for timestamp in format <span class="chatlog__timestamp" title="...">
    timestamp_match = re.search(r'<span class="chatlog__timestamp"[^>]*title="([^"]+)"', message_html)
    if not timestamp_match:
        return None
    
    date_string = timestamp_match.group(1)
    
    date_match = re.search(r"(\d{1,2}) (\w+) (\d{4})", date_string)
    if not date_match:
        return None
    
    return date_match.group(3)