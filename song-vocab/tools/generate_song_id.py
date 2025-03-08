import re
import unicodedata
from typing import Optional

def generate_song_id(artist: str, title: str) -> str:
    """
    Generate a URL-safe string from artist and title.
    
    Args:
        artist (str): The artist name
        title (str): The song title
        
    Returns:
        str: A URL-safe string combining artist and title
    """
    # Combine artist and title
    if not artist:
        combined = title
    else:
        combined = f"{artist}-{title}"
    
    # Normalize unicode characters
    combined = unicodedata.normalize('NFKD', combined)
    
    # Convert to lowercase
    combined = combined.lower()
    
    # Remove special characters and replace spaces with hyphens
    combined = re.sub(r'[^\w\s-]', '', combined)
    combined = re.sub(r'[\s]+', '-', combined)
    
    # Remove consecutive hyphens
    combined = re.sub(r'-+', '-', combined)
    
    # Trim hyphens from start and end
    combined = combined.strip('-')
    
    return combined