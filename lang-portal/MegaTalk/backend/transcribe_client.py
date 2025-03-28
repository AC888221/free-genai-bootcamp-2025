import boto3
import json
import time
from typing import Optional
import os
import sys
from datetime import datetime
import asyncio
import io
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent
import uuid  # Add this to the imports at the top

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from backend.config import logger, TRANSCRIBE_CONFIG, TRANSCRIBE_DEFAULTS
except ImportError:
    # Fallback for direct script execution
    from config import logger, TRANSCRIBE_CONFIG, TRANSCRIBE_DEFAULTS

class TranscriptHandler:
    def __init__(self):
        self.transcript = ""
        self.is_final = False
        logger.debug("Initialized new TranscriptHandler")
        
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        """Process transcript events according to the AWS Transcribe API structure"""
        if not transcript_event.transcript:
            logger.debug("Received empty transcript event")
            return
        
        for result in transcript_event.transcript.results:
            # Log result details for debugging
            logger.debug(f"Processing result: is_partial={result.is_partial}, "
                       f"result_id={result.result_id}, "
                       f"start_time={result.start_time}, "
                       f"end_time={result.end_time}")
            
            if not result.is_partial:
                if result.alternatives:
                    transcript_text = result.alternatives[0].transcript
                    self.transcript += transcript_text + " "
                    logger.debug(f"Added final transcript segment: {transcript_text}")
                else:
                    logger.debug("No alternatives found in result")

class TranscribeClient:
    def __init__(self):
        """Initialize Amazon Transcribe Streaming client"""
        try:
            # Use config for client initialization
            self.streaming_client = TranscribeStreamingClient(
                region=TRANSCRIBE_CONFIG.region_name,
                retry_config=TRANSCRIBE_CONFIG.retries  # Use retry config from settings
            )
            logger.info(f"Successfully initialized Transcribe client in region {TRANSCRIBE_CONFIG.region_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Transcribe client: {str(e)}")
            raise

    async def _stream_audio(self, audio_bytes: bytes, language_code: str) -> Optional[str]:
        """Internal method to handle streaming transcription"""
        try:
            handler = TranscriptHandler()
            logger.info(f"Starting transcription with handler for {len(audio_bytes)} bytes")
            
            # Use configuration for chunk size
            chunk_size = TRANSCRIBE_DEFAULTS.get("chunk_size", 1024 * 16)
            
            async def input_stream():
                stream = io.BytesIO(audio_bytes)
                total_chunks = 0
                total_bytes = 0
                while chunk := stream.read(chunk_size):
                    total_chunks += 1
                    total_bytes += len(chunk)
                    yield {
                        "AudioEvent": {
                            "AudioChunk": chunk
                        }
                    }
                logger.info(f"Finished reading audio: {total_chunks} chunks, {total_bytes} bytes")
            
            session_id = str(uuid.uuid4())
            logger.debug(f"Generated session ID: {session_id}")
            
            # Use all relevant config parameters
            stream = await self.streaming_client.start_stream_transcription(
                language_code=language_code,
                media_sample_rate_hz=TRANSCRIBE_DEFAULTS["sample_rate"],
                media_encoding=TRANSCRIBE_DEFAULTS["media_format"],
                session_id=session_id,
                enable_partial_results_stabilization=TRANSCRIBE_DEFAULTS.get("enable_partial_results_stabilization", True),
                partial_results_stability=TRANSCRIBE_DEFAULTS.get("partial_results_stability", "high"),
                show_speaker_label=TRANSCRIBE_DEFAULTS.get("show_speaker_label", False),
                enable_channel_identification=TRANSCRIBE_DEFAULTS.get("enable_channel_identification", False),
                vocabulary_name=TRANSCRIBE_DEFAULTS.get("vocabulary_name"),
                vocabulary_filter_name=TRANSCRIBE_DEFAULTS.get("vocabulary_filter_name"),
                vocabulary_filter_method=TRANSCRIBE_DEFAULTS.get("vocabulary_filter_method")
            )
            logger.info("Stream transcription started successfully")
            
            try:
                # Send audio chunks
                async for chunk in input_stream():
                    await stream.input_stream.send_audio_event(audio_chunk=chunk["AudioEvent"]["AudioChunk"])
                    logger.debug("Sent audio chunk")
                
                logger.info("Finished sending audio chunks")
                await stream.input_stream.end_stream()
                
                # Process transcription results
                logger.info("Starting to process transcription results")
                async for event in stream.output_stream:
                    if isinstance(event, TranscriptEvent):
                        await handler.handle_transcript_event(event)
                
                final_transcript = handler.transcript.strip()
                logger.info(f"Transcription completed: {len(final_transcript)} chars")
                return final_transcript
                
            finally:
                try:
                    await stream.input_stream.end_stream()
                except Exception as e:
                    logger.debug(f"Stream cleanup note: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error in streaming transcription: {str(e)}", exc_info=True)
            raise

    def transcribe_audio(self, audio_bytes: bytes, language_code: str = None) -> Optional[str]:
        """Transcribe audio using Amazon Transcribe streaming API"""
        try:
            if language_code is None:
                language_code = TRANSCRIBE_DEFAULTS["language_code"]
            
            logger.info(f"Starting streaming transcription with {len(audio_bytes)} bytes of audio")
            return asyncio.run(self._stream_audio(audio_bytes, language_code))
                
        except Exception as e:
            logger.error(f"Error in transcription: {str(e)}")
            return None

# Initialize global client
transcribe_client = TranscribeClient()

def transcribe_audio_file(audio_bytes: bytes, language_code: str = None) -> Optional[str]:
    """Wrapper function to transcribe audio using Amazon Transcribe"""
    return transcribe_client.transcribe_audio(audio_bytes, language_code)

# Update the standalone section
if __name__ == "__main__":
    import argparse
    import wave
    import logging
    
    # Configure logging for standalone mode if needed
    if 'logger' not in globals():
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger(__name__)  # Use __name__ instead of config's logger
    
    def read_wav_file(file_path: str) -> bytes:
        """Read a WAV file and return its PCM data"""
        try:
            with wave.open(file_path, 'rb') as wav_file:
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                frame_rate = wav_file.getframerate()
                
                logger.info(f"Audio properties: channels={channels}, "
                          f"sample_width={sample_width * 8}bit, "
                          f"frame_rate={frame_rate}Hz")
                
                # Use config values for validation
                if sample_width != TRANSCRIBE_DEFAULTS.get("sample_width", 2):
                    raise ValueError(f"Audio must be {TRANSCRIBE_DEFAULTS.get('sample_width', 2) * 8}-bit PCM "
                                  f"(current: {sample_width * 8}bit)")
                if frame_rate != TRANSCRIBE_DEFAULTS["sample_rate"]:
                    raise ValueError(f"Audio must be {TRANSCRIBE_DEFAULTS['sample_rate']}Hz "
                                  f"(current: {frame_rate}Hz). "
                                  f"Use ffmpeg to convert: ffmpeg -i input.wav -ar {TRANSCRIBE_DEFAULTS['sample_rate']} output.wav")
                if channels != TRANSCRIBE_DEFAULTS.get("channels", 1):
                    raise ValueError(f"Audio must be {TRANSCRIBE_DEFAULTS.get('channels', 1)} channel(s) "
                                  f"(current: {channels} channels). "
                                  f"Use ffmpeg to convert: ffmpeg -i input.wav -ac {TRANSCRIBE_DEFAULTS.get('channels', 1)} output.wav")
                
                return wav_file.readframes(wav_file.getnframes())
        except wave.Error as e:
            raise ValueError(f"Invalid or corrupted WAV file: {str(e)}")
        except FileNotFoundError:
            raise ValueError(f"Audio file not found: {file_path}")

    # Set up argument parser
    parser = argparse.ArgumentParser(description='Transcribe an audio file using Amazon Transcribe')
    parser.add_argument('audio_file', help='Path to the WAV file to transcribe')
    parser.add_argument('--language', default='zh-CN', help='Language code (default: zh-CN)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--info', action='store_true', help='Show audio file info without transcribing')
    
    args = parser.parse_args()
    
    # Set debug level if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)
        # Also set the config logger to DEBUG
        logging.getLogger('backend.config').setLevel(logging.DEBUG)
    
    try:
        # Read the audio file
        logger.info(f"Reading audio file: {args.audio_file}")
        
        if args.info:
            # Just show audio info and exit
            try:
                with wave.open(args.audio_file, 'rb') as wav_file:
                    print("\nAudio File Information:")
                    print(f"Channels: {wav_file.getnchannels()}")
                    print(f"Sample Width: {wav_file.getsampwidth() * 8}bit")
                    print(f"Frame Rate: {wav_file.getframerate()}Hz")
                    print(f"Frames: {wav_file.getnframes()}")
                    print(f"Duration: {wav_file.getnframes() / wav_file.getframerate():.2f} seconds")
                sys.exit(0)
            except Exception as e:
                logger.error(f"Error reading audio info: {str(e)}")
                sys.exit(1)
        
        audio_data = read_wav_file(args.audio_file)
        
        # Transcribe the audio
        logger.info(f"Transcribing audio (language: {args.language})...")
        transcript = transcribe_audio_file(audio_data, args.language)
        
        if transcript:
            print("\nTranscription result:")
            print(transcript)
        else:
            print("\nTranscription failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        sys.exit(1)