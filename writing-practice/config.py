# config.py

# Configuration settings
OCR_LANGUAGES = ['ch_sim', 'en']
BEDROCK_REGION = "us-east-1"
CLAUDE_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
API_URL = "http://localhost:5000"  # Add this line with your Flask server URL

ABOUT_TEXT = """
This app uses:
- Claude 3 Haiku on Amazon Bedrock
- pytesseract for character recognition
- Google TTS for pronunciation

Created for language learning bootcamp.
"""

WELCOME_TEXT = """
Welcome to the Putonghua Learning App! This app will help you practice writing Chinese characters.
"""