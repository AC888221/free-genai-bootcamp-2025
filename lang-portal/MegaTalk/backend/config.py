import os
import logging
import sys
from pathlib import Path
import boto3
from botocore.config import Config

# Set up logging directory in user's home
log_dir = os.path.join(os.path.expanduser('~'), '.megatalk', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'megatalk.log')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BASE_TIMEOUT = 30  # Base timeout in seconds for Bedrock API calls
TIMEOUT_PER_CHAR = 0.1  # Additional timeout per character in seconds

# Constants
AUDIO_DIR = Path("audio")
AUDIO_DIR.mkdir(exist_ok=True)

# AWS Configuration
AWS_REGION = "us-west-2"

# Bedrock Configuration
BEDROCK_CONFIG = Config(
    region_name=AWS_REGION,
    retries=dict(max_attempts=3)
)

BEDROCK_MODEL_ARN = "us.amazon.nova-micro-v1:0"
BEDROCK_SYSTEM_MESSAGE = """You are a friendly AI Putonghua buddy. Please answer all questions in Putonghua. 
Even if the user asks in English, please answer in Putonghua. Keep your answers natural and conversational, flowing naturally from previous responses.
Follow the language rules, topic focus, and formality level provided below.

Important Rules:
1. Always respond in Simplified Chinese characters (not pinyin)
2. Do not start with "你好！" unless this is your first response in a conversation.
3. Acknowledge the user's input without repeating it verbatim
4. Build on previous turns to create a natural conversation flow
5. Use varied language and sentence structures to keep the conversation engaging
6. Stay within the specified HSK level vocabulary
7. Maintain the requested formality level
8. Focus on the selected topics
9. If the user seems confused, provide gentle guidance"""

# Separate inference parameters
BEDROCK_INFERENCE_CONFIG = {
    "temperature": 0.9,
    "maxTokens": 1000,
    "topP": 0.9
}

# Additional model fields (separate from inference config)
BEDROCK_ADDITIONAL_FIELDS = {
    "inferenceConfig": {
        "topK": 20
    }
}

# Conversation Management Configuration
MAX_UNSUMMARIZED_TOKENS = 2000  # Maximum tokens for unsummarized history in chat context
CHARS_PER_TOKEN = 4  # Rough estimate of chars per token for Chinese/English mixed text

# Summary Section Markers
SUMMARY_SECTION_HEADER = "=== Previous Summary ==="
NEW_MESSAGES_SECTION_HEADER = "=== New Messages ==="

# Polly Configuration
POLLY_CONFIG = Config(
    region_name=AWS_REGION,
    retries=dict(max_attempts=3)
)

POLLY_DEFAULTS = {
    "voice_id": "Zhiyu",
    "pitch": "medium",
    "rate": "medium",
    "volume": "medium"
}

# Add to existing imports and AWS configuration
TRANSCRIBE_CONFIG = Config(
    region_name=AWS_REGION,
    retries=dict(
        max_attempts=3,
        mode='standard'
    )
)

# Add Transcribe defaults
TRANSCRIBE_DEFAULTS = {
    "language_code": "zh-CN",
    "sample_rate": 16000,
    "media_format": "pcm",
    "sample_width": 2,  # 16-bit
    "channels": 1,  # mono
    "chunk_size": 1024 * 16  # 16KB chunks
}

# Initialize Bedrock client
try:
    bedrock_client = boto3.client(
        'bedrock-runtime',
        config=BEDROCK_CONFIG
    )
    logger.info("Successfully initialized Bedrock client")
except Exception as e:
    logger.error(f"Failed to initialize Bedrock client: {e}")
    raise

def calculate_timeout(input_text):
    """Calculate timeout based on input text length."""
    return BASE_TIMEOUT + (len(input_text) * TIMEOUT_PER_CHAR)

