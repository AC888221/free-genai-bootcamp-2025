from youtube_transcript_api import YouTubeTranscriptApi
from typing import Optional, List, Dict
import os  # Bootcamp Week 2: Import os module
from googletrans import Translator  # Bootcamp Week 2: Import Google Translate API

class YouTubeTranscriptDownloader:
    def __init__(self, languages: List[str] = ["zh-Hans", "en"]):  # Bootcamp Week 2: Added English as a fallback language
        self.languages = languages
        self.translator = Translator()  # Bootcamp Week 2: Initialize the Google Translator

    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from YouTube URL
        
        Args:
            url (str): YouTube URL
            
        Returns:
            Optional[str]: Video ID if found, None otherwise
        """
        if "v=" in url:
            return url.split("v=")[1][:11]
        elif "youtu.be/" in url:
            return url.split("youtu.be/")[1][:11]
        return None

    def get_transcript(self, video_id: str) -> Optional[List[Dict]]:
        """
        Download YouTube Transcript
        
        Args:
            video_id (str): YouTube video ID or URL
            
        Returns:
            Optional[List[Dict]]: Transcript if successful, None otherwise
        """
        # Extract video ID if full URL is provided
        if "youtube.com" in video_id or "youtu.be" in video_id:
            video_id = self.extract_video_id(video_id)
            
        if not video_id:
            print("Invalid video ID or URL")
            return None

        print(f"Downloading transcript for video ID: {video_id}")
        try:
            available_transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
            print(f"Available transcripts: {available_transcripts}")
        except Exception as e:
            print(f"Failed to list transcripts: {str(e)}")
            return None        

        # list all available transcripts
        try:
            available_transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
            print(f"Available transcripts: {available_transcripts}")
        except Exception as e:
            print(f"Failed to list transcripts: {str(e)}")
            return None

        # Attempt to download the Simplified Chinese transcript
        try:
            print("Trying to download Simplified Chinese transcript...") # Bootcamp Week 2: logging and debugging
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["zh-Hans"])
            print("Simplified Chinese transcript downloaded successfully.") # Bootcamp Week 2: logging and debugging
            return transcript
        except Exception as e:
            print(f"Simplified Chinese transcript not available: {str(e)}")
            # Bootcamp Week 2: Attempt to download the English transcript as a fallback
            try:
                print("Trying to download English transcript as fallback...") # Bootcamp Week 2: logging and debugging
                english_transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
                print("English transcript downloaded successfully.")
                print("Translating English transcript to Simplified Chinese...") # Bootcamp Week 2: logging and debugging
                translated_transcript = self.translate_transcript(english_transcript, target_language="zh-CN")
                print("Translation completed successfully.") # Bootcamp Week 2: logging and debugging
                return translated_transcript
            except Exception as e:
                print(f"Failed to download English transcript: {str(e)}") 
                return None

    def translate_transcript(self, english_transcript: List[Dict], target_language: str = "zh-CN") -> List[Dict]:
        """
        Translate English transcript to the target language.
        
        Args:
            english_transcript (List[Dict]): The English transcript to translate.
            target_language (str): The target language code (e.g., 'zh-Hans').
            
        Returns:
            List[Dict]: Translated transcript.
        """
        # Bootcamp Week 2: Create a new list to hold the translated transcript
        translated = []
        for entry in english_transcript:
            # Bootcamp Week 2: Use Google Translate to translate the text
            try:
                print(f"Translating text: {entry['text']} to {target_language}")
                translated_text = self.translator.translate(entry['text'], dest=target_language).text
                translated.append({
                    'text': translated_text,
                    'start': entry['start'],
                    'duration': entry['duration']
                })
            except Exception as e:
                print(f"Translation error for text '{entry['text']}': {str(e)}")
        return translated

    def save_transcript(self, transcript: List[Dict], filename: str) -> bool:
        """
        Save transcript to file
        
        Args:
            transcript (List[Dict]): Transcript data
            filename (str): Output filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        directory = os.path.join(os.path.dirname(__file__), 'data', 'transcripts') # Bootcamp Week 2: Ensure the directory exists
        if not os.path.exists(directory):
            os.makedirs(directory)  # Bootcamp Week 2: Create the directory if it doesn't exist

        filename = f"{directory}/{filename}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for entry in transcript:
                    f.write(f"{entry['text']}\n")
            return True
        except Exception as e:
            print(f"Error saving transcript: {str(e)}")
            return False

def main(video_url, print_transcript=False):
    # Initialize downloader
    downloader = YouTubeTranscriptDownloader()
    
    # Get transcript
    transcript = downloader.get_transcript(video_url)
    
    if transcript:
        # Save transcript
        video_id = downloader.extract_video_id(video_url)
        if downloader.save_transcript(transcript, video_id):
            print(f"Transcript saved successfully to {video_id}.txt")
            # Print transcript if True
            if print_transcript:
                for entry in transcript:
                    print(f"{entry['text']}")
        else:
            print("Failed to save transcript")
    else:
        print("Failed to get transcript")

if __name__ == "__main__":
    video_url = "https://www.youtube.com/watch?v=KQpXjP0jSsY"
    main(video_url, print_transcript=True)