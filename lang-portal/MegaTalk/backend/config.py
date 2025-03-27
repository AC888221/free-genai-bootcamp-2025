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

BEDROCK_INFERENCE_CONFIG = {
    "temperature": 0.7,
    "maxTokens": 128000
}

# Conversation Management Configuration
MAX_HISTORY_LENGTH = 10  # Number of message pairs before summarizing

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

def get_summary_prompt(conversation: str) -> str:
    """Generate a prompt for conversation summarization."""
    return f"""Please provide a brief summary of the following conversation, 
capturing the main topics discussed and any important points. Keep the summary concise:

{conversation}

Summary:""" 