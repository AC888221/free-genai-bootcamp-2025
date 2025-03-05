# config.py

# Configuration settings
OCR_LANGUAGES = ['ch_sim', 'en']
BEDROCK_REGION = "us-east-1"
CLAUDE_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
API_URL = "http://localhost:5000"  # Add this line with your Flask server URL

STYLING = """
<style>
    .main-header {
        font-size: 2.5rem;
        color: #FF4B4B;
        text-align: center;
    }
    .sub-header {
        font-size: 1.5rem;
        margin-bottom: 1rem;
    }
    .chinese-text {
        font-size: 2rem;
        color: #FF4B4B;
        margin: 1rem 0;
    }
    .pinyin-text {
        font-size: 1.2rem;
        color: #636EFA;
        margin-bottom: 1.5rem;
    }
    .instruction-text {
        font-size: 1rem;
        color: #7F7F7F;
        margin: 1rem 0;
    }
    .grade-s {color: #00CC96;}
    .grade-a {color: #636EFA;}
    .grade-b {color: #FFA15A;}
    .grade-c {color: #EF553B;}
    .grade-d {color: #AB63FA;}
    .char-correct {
        color: #00CC96;
        font-weight: bold;
    }
    .char-incorrect {
        color: #EF553B;
        text-decoration: line-through;
    }
    .stApp {
        max-width: 800px;
        margin: 0 auto;
    }
</style>
"""

ABOUT_TEXT = """
This app uses:
- Claude 3 Haiku on Amazon Bedrock
- pytesseract for character recognition
- Google TTS for pronunciation

Created for language learning bootcamp.
"""

WELCOME_TEXT = """
Welcome to the Putonghua Learning App! This app will help you practice writing Chinese characters.

Press the button below to get started with a random Chinese sentence.

"""