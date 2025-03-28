import boto3
import json
import time
from typing import Optional
import os
import sys
from datetime import datetime
from backend.config import logger, TRANSCRIBE_CONFIG, TRANSCRIBE_DEFAULTS

# Add the parent directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TranscribeClient:
    def __init__(self):
        """Initialize Amazon Transcribe client"""
        try:
            self.transcribe_client = boto3.client('transcribe', config=TRANSCRIBE_CONFIG)
            self.s3_client = boto3.client('s3')
            logger.info("Successfully initialized Transcribe client")
        except Exception as e:
            logger.error(f"Failed to initialize Transcribe client: {str(e)}")
            raise

    def transcribe_audio(self, audio_bytes: bytes, language_code: str = None) -> Optional[str]:
        """Transcribe audio using Amazon Transcribe"""
        try:
            if language_code is None:
                language_code = TRANSCRIBE_DEFAULTS["language_code"]
            
            logger.info(f"Starting transcription job with {len(audio_bytes)} bytes of audio")
            
            job_name = f"megatalk_transcription_{int(time.time())}"
            response = self.transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaData': audio_bytes},
                MediaFormat=TRANSCRIBE_DEFAULTS["media_format"],
                LanguageCode=language_code,
                Settings={
                    'ShowSpeakerLabels': False,
                    'EnableAutomaticPunctuation': True
                }
            )
            
            logger.info(f"Transcription job {job_name} started")
            
            # Wait for completion
            while True:
                status = self.transcribe_client.get_transcription_job(
                    TranscriptionJobName=job_name
                )
                if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
                    break
                time.sleep(1)
            
            if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
                logger.info(f"Transcription job {job_name} completed successfully")
                return status['TranscriptionJob']['Transcript']['TranscriptFileUri']
            else:
                logger.error(f"Transcription job {job_name} failed")
                return None
                
        except Exception as e:
            logger.error(f"Error in transcription: {str(e)}")
            return None

# Initialize global client
transcribe_client = TranscribeClient()

def transcribe_audio_file(audio_bytes: bytes, language_code: str = "zh-CN") -> Optional[str]:
    """Wrapper function to transcribe audio using Amazon Transcribe"""
    return transcribe_client.transcribe_audio(audio_bytes, language_code)