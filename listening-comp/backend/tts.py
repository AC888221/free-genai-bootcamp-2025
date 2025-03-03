import os
import boto3
import subprocess
import logging
from time import sleep
from contextlib import contextmanager
import json
from typing import Optional
from pydub import AudioSegment  # Importing pydub for audio length calculation
import filetype  # Importing filetype for format verification

# Initialize Amazon Polly client
polly_client = boto3.client('polly')

# Model ID
MODEL_ID = "amazon.nova-micro-v1:0"
MAX_TOKENS = 16385  # Example maximum token limit for the model
ADJUSTED_MAX_TOKENS = int(MAX_TOKENS * 0.9)  # Reduce by 10% for leeway

class BedrockChat:
    def __init__(self, model_id: str = MODEL_ID):
        """Initialize Bedrock chat client"""
        self.bedrock_client = boto3.client('bedrock-runtime', region_name="us-east-1")
        self.model_id = model_id

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the text"""
        return len(text.split())

    def analyze_text(self, text: str) -> Optional[list]:
        """Analyze text using Amazon Bedrock"""
        input_token_count = self.count_tokens(text)
        available_tokens_for_output = ADJUSTED_MAX_TOKENS - input_token_count - 50  # Subtracting extra tokens for prompt overhead

        logging.info(f"Input token count: {input_token_count}")
        logging.info(f"Available tokens for output: {available_tokens_for_output}")

        prompt = f"""
        Identify the different speakers in the following text and provide the output in a structured JSON format. Return only the JSON content without any additional text or formatting. Ensure the output does not exceed {available_tokens_for_output} tokens. The JSON content must be enclosed within [START_JSON] and [END_JSON] tags:

        {text}

        Provide the output in the following format:
        [START_JSON]
        [
            {{"speaker": "Speaker 1", "text": "Dialogue 1"}},
            {{"speaker": "Speaker 2", "text": "Dialogue 2"}},
            ...
        ]
        [END_JSON]
        """
        
        messages = [{
            "role": "user",
            "content": [{"text": prompt}]
        }]

        try:
            response = self.bedrock_client.converse(
                modelId=self.model_id,
                messages=messages,
                inferenceConfig={"temperature": 0.7}
            )
            logging.info(f"Response from Bedrock: {response}")
            # Extract the text content from the response
            content = response['output']['message']['content'][0]['text']
            logging.info(f"Extracted content: {content}")
            # Check for the presence of both tags
            start_idx = content.find("[START_JSON]")
            end_idx = content.find("[END_JSON]")
            logging.info(f"Start index: {start_idx}, End index: {end_idx}")
            if start_idx == -1 or end_idx == -1:
                logging.error("JSON tags not found in the response content")
                # Cap the output to a manageable amount and filter out repetitive content
                capped_content = content[:500] + '...' if len(content) > 500 else content
                filtered_content = ''.join([c for c in capped_content if c.isprintable()])
                logging.error(f"Full response content (filtered and capped): {filtered_content}")
                return None
            start_idx += len("[START_JSON]")
            json_content = content[start_idx:end_idx].strip()
            logging.info(f"Extracted JSON content: {json_content}")
            # Check if the content is in JSON format
            try:
                json_response = json.loads(json_content)
                logging.info(f"Parsed JSON response: {json_response}")
                return json_response
            except json.JSONDecodeError as e:
                logging.error(f"JSONDecodeError: {e}")
                logging.error("Response content is not in JSON format")
                return None
        except Exception as e:
            logging.error(f"Error invoking Bedrock model: {str(e)}")
            return None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@contextmanager
def open_file(file_path, mode, encoding=None):
    try:
        file = open(file_path, mode, encoding=encoding)
        yield file
    finally:
        file.close()

def generate_audio(text, voice_id='Zhiyu', pitch="medium", rate="medium", volume="medium", retries=3):
    ssml_text = f'<speak><prosody pitch="{pitch}" rate="{rate}" volume="{volume}">{text}</prosody></speak>'
    for attempt in range(retries):
        try:
            response = polly_client.synthesize_speech(Text=ssml_text, VoiceId=voice_id, OutputFormat='mp3', TextType='ssml')
            return response['AudioStream'].read()
        except boto3.exceptions.Boto3Error as e:
            logging.error(f"Error generating audio (attempt {attempt + 1}): {e}")
            if attempt < retries - 1:
                sleep(2 ** attempt)  # Exponential backoff
            else:
                return None

def process_text_files(input_dir, output_dir):
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    bedrock_chat = BedrockChat()

    for filename in os.listdir(input_dir):
        if filename.endswith('.txt'):
            audio_parts = []
            list_filename = None
            try:
                logging.info(f"Processing file: {filename}")
                with open_file(os.path.join(input_dir, filename), 'r', encoding='utf-8') as file:
                    text = file.read()
                    speakers_text = bedrock_chat.analyze_text(text)
                    if speakers_text:
                        total_audio_length = 0
                        for i, speaker in enumerate(speakers_text):
                            pitch, rate, volume = ("high", "slow", "loud") if i % 2 == 0 else ("low", "x-slow", "soft")
                            if i > 0:
                                audio_parts.append(generate_audio('<break time="3s"/>', 'Zhiyu'))  # Increased pause to 3 seconds
                            audio = generate_audio(speaker['text'], 'Zhiyu', pitch, rate, volume)
                            if audio is None:
                                logging.error("Audio generation failed")
                                raise Exception("Failed to generate audio")
                            # Generate shorter file names
                            short_filename = f"p{i}.mp3"
                            audio_filename = os.path.abspath(os.path.join(output_dir, short_filename))
                            with open_file(audio_filename, 'wb') as audio_file:
                                audio_file.write(audio)
                            if not os.path.exists(audio_filename):
                                raise Exception(f"Audio file {audio_filename} was not created")
                            audio_parts.append(audio_filename)
                            audio_length = AudioSegment.from_file(audio_filename).duration_seconds
                            total_audio_length += audio_length
                            logging.info(f"Generated audio file: {audio_filename} (length: {audio_length} seconds)")
                            
                            # Verify audio file integrity
                            try:
                                audio_segment = AudioSegment.from_file(audio_filename)
                                logging.info(f"Verified audio file: {audio_filename} (length: {audio_segment.duration_seconds} seconds)")
                                # Check audio file format
                                kind = filetype.guess(audio_filename)
                                if kind is None or kind.mime.split('/')[0] != 'audio':
                                    raise Exception(f"Invalid audio file format: {audio_filename}")
                                logging.info(f"Audio file format: {kind.mime}")
                            except Exception as e:
                                logging.error(f"Error verifying audio file {audio_filename}: {e}")
                                raise Exception(f"Audio file {audio_filename} is corrupted or has an invalid format")
                        
                        logging.info(f"Number of audio files created: {len(audio_parts)}")
                        logging.info(f"Total length of all audio files: {total_audio_length} seconds")

                        list_filename = os.path.abspath(os.path.join(output_dir, f"{filename[:10]}_list.txt"))
                        with open_file(list_filename, 'w', encoding='utf-8') as list_file:
                            for audio_part in audio_parts:
                                if os.path.exists(audio_part):
                                    list_file.write(f"file '{audio_part}'\n")
                                else:
                                    logging.error(f"Audio part does not exist: {audio_part}")
                        logging.info(f"Created list file for ffmpeg: {list_filename}")
                        
                        # Use the original filename (without .txt) for the final audio file name
                        final_audio_filename = os.path.abspath(os.path.join(output_dir, f"audio_{filename[:-4]}.mp3"))
                        logging.info(f"Final audio file will be: {final_audio_filename}")
                        subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_filename, '-c', 'copy', final_audio_filename, '-y', '-loglevel', 'verbose'])
                        
                        final_audio_length = AudioSegment.from_file(final_audio_filename).duration_seconds
                        length_lost = total_audio_length - final_audio_length
                        logging.info(f"Number of audio files combined: {len(audio_parts)}")
                        logging.info(f"Length of the final combined audio file: {final_audio_length} seconds")
                        logging.info(f"Length lost during concatenation: {length_lost} seconds")
            except Exception as e:
                logging.error(f"Error processing file {filename}: {e}")
            finally:
                for audio_part in audio_parts:
                    if os.path.exists(audio_part):
                        logging.info(f"Deleting temporary audio file: {audio_part}")
                        os.remove(audio_part)
                if list_filename and os.path.exists(list_filename):
                    logging.info(f"Deleting list file: {list_filename}")
                    os.remove(list_filename)
                logging.info(f"Cleaned up temporary files for {filename}")

if __name__ == '__main__':
    input_dir = os.getenv('INPUT_DIR', 'backend/data/int_resp/')
    output_dir = os.getenv('OUTPUT_DIR', 'backend/data/audio/')
    process_text_files(input_dir, output_dir)