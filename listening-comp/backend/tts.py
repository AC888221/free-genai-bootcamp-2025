import os
import boto3
import subprocess
import logging
from time import sleep
from contextlib import contextmanager

# Initialize Amazon Polly client
polly_client = boto3.client('polly')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@contextmanager
def open_file(file_path, mode):
    try:
        file = open(file_path, mode)
        yield file
    finally:
        file.close()

def generate_audio(text, voice_id='Zhiyu', pitch="medium", rate="medium", volume="medium", retries=3):
    ssml_text = f'<speak><prosody pitch="{pitch}" rate="{rate}" volume="{volume}">{text}</prosody></speak>'
    for attempt in range(retries):
        try:
            response = polly_client.synthesize_speech(Text=ssml_text, VoiceId=voice_id, OutputFormat='mp3', TextType='ssml')
            return response['AudioStream'].read()
        except Exception as e:
            logging.error(f"Error generating audio (attempt {attempt + 1}): {e}")
            if attempt < retries - 1:
                sleep(2 ** attempt)  # Exponential backoff
            else:
                return None

def analyze_speakers(text):
    # Placeholder function to simulate speaker analysis
    speakers = [
        {'text': '你好，你好吗？', 'gender': 'male'},
        {'text': '我很好，谢谢你！', 'gender': 'female'},
        {'text': '你呢？', 'gender': 'male'}
    ]
    return speakers

def process_text_files(input_dir, output_dir):
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    for filename in os.listdir(input_dir):
        if filename.endswith('.txt'):
            audio_parts = []
            list_filename = None
            try:
                with open_file(os.path.join(input_dir, filename), 'r') as file:
                    text = file.read()
                    speakers = analyze_speakers(text)
                    for i, speaker in enumerate(speakers):
                        pitch, rate, volume = ("high", "slow", "loud") if i % 2 == 0 else ("low", "x-slow", "soft")
                        if i > 0:
                            audio_parts.append(generate_audio('<break time="3s"/>', 'Zhiyu'))  # Increased pause to 3 seconds
                        audio = generate_audio(speaker['text'], 'Zhiyu', pitch, rate, volume)
                        if audio is None:
                            raise Exception("Failed to generate audio")
                        audio_filename = os.path.abspath(os.path.join(output_dir, f"{filename.replace('.txt', '')}_p{i}.mp3"))
                        with open_file(audio_filename, 'wb') as audio_file:
                            audio_file.write(audio)
                        if not os.path.exists(audio_filename):
                            raise Exception(f"Audio file {audio_filename} was not created")
                        audio_parts.append(audio_filename)
                        logging.info(f"Generated audio file: {audio_filename}")
                    
                    list_filename = os.path.abspath(os.path.join(output_dir, f"{filename.replace('.txt', '')}_list.txt"))
                    with open_file(list_filename, 'w', encoding='utf-8') as list_file:
                        for audio_part in audio_parts:
                            list_file.write(f"file '{audio_part}'\n")
                    logging.info(f"Created list file for ffmpeg: {list_filename}")
                    
                    with open_file(list_filename, 'r', encoding='utf-8') as list_file:
                        list_contents = list_file.read()
                        logging.info(f"Contents of the list file:\n{list_contents}")
                    
                    final_audio_filename = os.path.abspath(os.path.join(output_dir, filename.replace('.txt', '.mp3')))
                    logging.info(f"Final audio file will be: {final_audio_filename}")
                    subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_filename, '-c', 'copy', final_audio_filename])
            except Exception as e:
                logging.error(f"Error processing file {filename}: {e}")
            finally:
                for audio_part in audio_parts:
                    if os.path.exists(audio_part):
                        os.remove(audio_part)
                if list_filename and os.path.exists(list_filename):
                    os.remove(list_filename)
                logging.info(f"Cleaned up temporary files for {filename}")

if __name__ == '__main__':
    input_dir = os.getenv('INPUT_DIR', 'backend/data/int_resp/')
    output_dir = os.getenv('OUTPUT_DIR', 'backend/data/audio/')
    process_text_files(input_dir, output_dir)