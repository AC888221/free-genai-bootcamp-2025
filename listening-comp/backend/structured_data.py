import boto3
from typing import Optional, List, Dict
import os
from pathlib import Path

class HSK2TranscriptProcessor:
    def __init__(self, model_id: str = "amazon.nova-micro-v1:0"):
        """Initialize Bedrock client for transcript processing"""
        self.bedrock_client = boto3.client('bedrock-runtime', region_name="us-east-1")
        self.model_id = model_id

    def _generate_prompt(self, transcript: str) -> str:
        """Generate prompt for the Bedrock model"""
        return f"""This HSK 2 listening test transcript has 4 sections.
        Section 1 has 10 questions, Section 2 has 10 questions. Section 3 has 10 questions. Section 4 has 5 questions.
        Remove any introductory text from the start of the test and each section.
        Remove any consecutively repeated lines.
        Make sure each question is numbered and that the number is in simplified Chinese, e.g., "一：", "二：", "三：", "四：", etc.
        Make sure there is no text before the first question.
        Here is the transcript:

        {transcript}

        Return only the processed text without any JSON formatting."""

    def _process_with_bedrock(self, prompt: str) -> Optional[str]:
        """Process text using Amazon Bedrock"""
        messages = [{
            "role": "user",
            "content": [{"text": prompt}]
        }]

        try:
            response = self.bedrock_client.converse(
                modelId=self.model_id,
                messages=messages,
                inferenceConfig={"temperature": 0.1}  # Low temperature for more focused extraction
            )
            processed_text = response['output']['message']['content'][0]['text']
            
            # Post-processing to remove any remaining repetitive lines
            lines = processed_text.split('\n')
            unique_lines = []
            seen = set()
            for line in lines:
                if line not in seen:
                    unique_lines.append(line)
                    seen.add(line)
            return '\n'.join(unique_lines)
        except Exception as e:
            print(f"Error processing with Bedrock: {str(e)}")
            return None

    def process_transcript(self, transcript_path: str) -> Optional[str]:
        """Process a single transcript file"""
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript = f.read()
            
            prompt = self._generate_prompt(transcript)
            processed_text = self._process_with_bedrock(prompt)
            return processed_text
        except Exception as e:
            print(f"Error processing transcript {transcript_path}: {str(e)}")
            return None

    def process_directory(self, directory_path: str) -> Dict[str, Optional[str]]:
        """Process all transcript files in a directory"""
        results = {}
        directory = Path(directory_path)
        
        for file_path in directory.glob('*.txt'):
            results[file_path.name] = self.process_transcript(str(file_path))
            
        return results

if __name__ == "__main__":
    # Example usage
    processor = HSK2TranscriptProcessor()
    transcripts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'transcripts')
    results = processor.process_directory(transcripts_dir)
    
    for filename, processed_text in results.items():
        if processed_text:
            print(f"\nProcessed {filename}:")
            print(processed_text)