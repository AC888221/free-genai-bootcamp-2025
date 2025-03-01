import boto3
from typing import Optional, List, Dict
import os
from pathlib import Path
import hashlib

class HSK2TranscriptProcessor:
    def __init__(self, model_id: str = "amazon.nova-micro-v1:0"):
        """Initialize Bedrock client for transcript processing"""
        self.bedrock_client = boto3.client('bedrock-runtime', region_name="us-east-1")
        self.model_id = model_id

    def _generate_prompt(self, transcript: str) -> str:
        """Generate prompt for the Bedrock model"""
        return f"""This HSK 2 listening test transcript has 4 sections.
        Section 1 has 10 questions, Section 2 has 10 questions, Section 3 has 10 questions, and Section 4 has 5 questions.
        Remove any introductory text from the start of the test and each section.
        Remove any consecutively repeated lines.
        Make sure each question is numbered in simplified Chinese characters followed by a colon and a space, e.g., "一： ", "二： ", "三： ", "四： ", etc.
        Ensure there is no text before the first question.
        Remove any empty lines and extra spaces before or after the questions.
        Here is the transcript:

        {transcript}

        Return only the processed text without any JSON formatting."""

    def _generate_id(self, filename: str, question_number: int) -> str:
        """Generate a consistent ID for a question based on the filename and question number"""
        return f"{filename}_q{question_number}"

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

    def process_transcript(self, transcript_path: str, output_dir: str) -> Optional[str]:
        """Process a single transcript file and save the processed text"""
        try:
            filename = Path(transcript_path).stem
            output_path_qsec3 = os.path.join(output_dir, 'qsec3', f"{filename}_q21.txt")
            output_path_qsec4 = os.path.join(output_dir, 'qsec4', f"{filename}_q31.txt")
            
            # Check if the output files already exist
            section3_exists = os.path.exists(output_path_qsec3)
            section4_exists = os.path.exists(output_path_qsec4)
            
            if section3_exists and section4_exists:
                print(f"Transcript {transcript_path} has already been processed.")
                return None
            
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript = f.read()
            
            prompt = self._generate_prompt(transcript)
            processed_text = self._process_with_bedrock(prompt)
            
            if processed_text:
                # Split the processed text into individual questions
                lines = processed_text.split('\n')
                questions = [line for line in lines if line.strip() and "：" in line]
                
                # Save each question individually in their respective section folders
                for i, question in enumerate(questions, start=1):
                    # Skip sections 1 and 2
                    if i <= 20:
                        continue
                    
                    section = 'qsec3' if 21 <= i <= 30 else 'qsec4'
                    section_dir = os.path.join(output_dir, section)
                    if not os.path.exists(section_dir):
                        os.makedirs(section_dir)
                    
                    question_id = self._generate_id(filename, i)
                    question_path = os.path.join(section_dir, f"{question_id}.txt")
                    with open(question_path, 'w', encoding='utf-8') as f:
                        f.write(question)
                    print(f"Saved question to {question_path}")
                
                return processed_text
            else:
                print(f"Failed to process transcript {transcript_path}")
                return None
        except Exception as e:
            print(f"Error processing transcript {transcript_path}: {str(e)}")
            return None

    def process_directory(self, input_dir: str, output_dir: str) -> Dict[str, Optional[str]]:
        """Process all transcript files in a directory"""
        results = {}
        input_directory = Path(input_dir)
        
        for file_path in input_directory.glob('*.txt'):
            results[file_path.name] = self.process_transcript(str(file_path), output_dir)
            
        return results

if __name__ == "__main__":
    # Example usage
    processor = HSK2TranscriptProcessor(model_id="amazon.nova-micro-v1:0")
    transcripts_dir = os.path.join(os.path.dirname(__file__), 'data', 'transcripts')
    questions_dir = os.path.join(os.path.dirname(__file__), 'data')
    
    if not os.path.exists(questions_dir):
        os.makedirs(questions_dir)
    
    results = processor.process_directory(transcripts_dir, questions_dir)
    
    for filename, processed_text in results.items():
        if processed_text:
            print(f"\nProcessed {filename}:")
            print(processed_text)