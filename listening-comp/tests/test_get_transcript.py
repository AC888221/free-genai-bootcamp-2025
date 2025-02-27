import sys
import os

# Bootcamp Week 2: Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from backend.get_transcript import YouTubeTranscriptDownloader
from typing import List, Dict

def test_transcript_download():
    downloader = YouTubeTranscriptDownloader()
    video_url = "https://www.youtube.com/watch?v=PO3sdqBbXEo"
    transcript = downloader.get_transcript(video_url)
    assert transcript is not None, "Transcript should not be None"
    assert isinstance(transcript, list), "Transcript should be a list"

def test_translate_transcript():
    downloader = YouTubeTranscriptDownloader()
    # Bootcamp Week 2: Sample English transcript for testing
    english_transcript = [
        {'text': 'Hello, how are you?', 'start': 0, 'duration': 2},
        {'text': 'This is a test.', 'start': 2, 'duration': 2}
    ]
    # Bootcamp Week 2: Translate the English transcript to Simplified Chinese using 'zh-cn'
    translated = downloader.translate_transcript(english_transcript, target_language='zh-cn')  # Use 'zh-cn'
    
    # Bootcamp Week 2: Ensure the translated transcript is not None
    assert translated is not None, "Translated transcript should not be None"
    # Bootcamp Week 2: Ensure the translated transcript is a list
    assert isinstance(translated, list), "Translated transcript should be a list"
    # Bootcamp Week 2: Ensure each entry in the translated transcript has a 'text' key
    assert all('text' in entry for entry in translated), "Each entry should have a 'text' key"

# Run the tests
if __name__ == "__main__":
    pytest.main()
