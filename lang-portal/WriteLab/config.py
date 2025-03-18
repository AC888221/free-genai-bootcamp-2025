# config.py

# Configuration settings
OCR_LANGUAGES = ['ch_sim', 'en']
BEDROCK_REGION = "us-west-2"
CLAUDE_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"

# Lang-portal server configuration
LANG_PORTAL_URL = "http://localhost:5000"  # URL for the lang-portal server that manages word collections

ABOUT_TEXT = """
This app uses:
- Claude 3 Haiku on Amazon Bedrock for sentence generation
- Pytesseract for character recognition
- Google TTS for pronunciation
- Lang-portal server for word collections

Created for language learning bootcamp.
"""

WELCOME_TEXT = """
Welcome to WriteLab! This app will help you practice writing Putonghua characters.

1. Look at your word collection (synced with lang-portal)
2. Practice writing Putonghua characters
3. Submit your writing for grading and feedback
"""