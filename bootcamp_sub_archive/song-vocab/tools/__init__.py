# Import all tools for easier access
from .search_web import search_web
from .get_page_content import get_page_content
from .extract_vocabulary import extract_vocabulary
from .generate_song_id import generate_song_id

__all__ = [
    'search_web',
    'get_page_content',
    'extract_vocabulary',
    'generate_song_id'
]