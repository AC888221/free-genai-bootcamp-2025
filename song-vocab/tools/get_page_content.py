import requests
from requests.exceptions import RequestException
from html2text import HTML2Text
import re

def get_page_content(url: str) -> str:
    """
    Get the content of a web page and convert it to markdown text.
    
    Args:
        url (str): The URL of the web page
        
    Returns:
        str: The content of the web page as markdown text
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Convert HTML to markdown
        h = HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.ignore_tables = False
        h.single_line_break = True
        h.unicode_snob = True  # Keep unicode characters

        content = h.handle(response.text)
        
        # Clean up the content
        content = clean_content(content)
        
        # Limit content length to avoid excessive token usage
        return content[:10000] if len(content) > 10000 else content
    except RequestException as e:
        return f"Error fetching page: {str(e)}"
    except Exception as e:
        return f"Error processing page: {str(e)}"

def clean_content(content: str) -> str:
    """
    Clean up the content by removing excess whitespace and formatting.
    
    Args:
        content (str): The content to clean
        
    Returns:
        str: The cleaned content
    """
    # Remove multiple consecutive blank lines
    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
    
    # Remove non-printable characters
    content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)
    
    # Remove HTML entity references that might have survived
    content = re.sub(r'&[a-zA-Z]+;', ' ', content)
    
    return content.strip()