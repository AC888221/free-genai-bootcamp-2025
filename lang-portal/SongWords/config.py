import os
import logging
import sys
from pathlib import Path

# Set up logging directory in user's home
log_dir = os.path.join(os.path.expanduser('~'), '.songwords', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'songwords.log')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Logging Configuration
LOG_CONFIG = {
    "level": logging.INFO,
    "format": '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}

# Database Configuration
DB_PATH = Path(__file__).parent / "songwords.db"
LANG_PORTAL_URL = "http://localhost:5000"

# Web Scraping & Search Configuration
SEARCH_CONFIG = {
    "timeout": 30,                     # Used for both search and scraping timeouts
    "max_retries": 3,
    "excluded_sites_path": Path(__file__).parent / "excluded_sites.json"
}

# AWS Configuration
AWS_CONFIG = {
    "region": os.getenv("AWS_REGION", "us-east-1"),
    "service": "bedrock-runtime",
    "retries": {
        "max_attempts": 3,
        "mode": "standard"
    }
}

# Model Configuration
MODEL_CONFIG = {
    "temperature": 0.7,
    "max_tokens": 2048,        # Updated to match implementation
    "model_id": "anthropic.claude-3-sonnet-20240229-v1:0"  # Updated to Claude 3 Sonnet
}

# Agent Configuration (now only contains agent-specific settings)
AGENT_CONFIG = {
    "exclusion_duration_hours": 24,
    "parent_exclusion_threshold": 3
}

# Supported Languages
LANGUAGES = {
    "zh-CN": "Chinese (Simplified)",
    "en-US": "English",
    "ja-JP": "Japanese",
    "ko-KR": "Korean"
}

# UI Configuration
UI_CONFIG = {
    "title": "SongWords - Language Learning Through Music",
    "icon": "🎵",
    "layout": "wide"
} 