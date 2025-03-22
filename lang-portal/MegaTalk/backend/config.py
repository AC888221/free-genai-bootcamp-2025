import os
import logging
import sys
from pathlib import Path
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

# Add Bedrock configuration
BEDROCK_CONFIG = Config(
    region_name=os.getenv("AWS_REGION", "us-west-2"),
    retries={
        'max_attempts': 3,
        'mode': 'standard'
    },
    connect_timeout=BASE_TIMEOUT,
    read_timeout=BASE_TIMEOUT
)

def calculate_timeout(input_text):
    """Calculate timeout based on input text length."""
    return BASE_TIMEOUT + (len(input_text) * TIMEOUT_PER_CHAR) 