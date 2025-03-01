import boto3
from typing import Optional, List, Dict
import os
from pathlib import Path
import hashlib
import pickle

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
        Remove any empty lines.
        Here is the transcript:

        {transcript}

        Return only the processed text without any JSON formatting."""

    def _generate_id(self, text: str) -> str:
        """Generate a consistent ID for a question"""
        return hashlib.md5(text.encode()).hexdigest()

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
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript = f.read()
            
            prompt = self._generate_prompt(transcript)
            processed_text = self._process_with_bedrock(prompt)
            
            if processed_text:
                # Split the processed text into sections
                lines = processed_text.split('\n')
                section3 = '\n'.join(lines[20:30])  # Questions 二十一 to 三十
                section4 = '\n'.join(lines[30:35])  # Questions 三十一 to 三十五
                
                # Save to files in /data/questions/ directory
                questions_dir = os.path.join(output_dir, 'questions')  # Path to 'questions'
                
                # Create the main questions directory if it doesn't exist
                if not os.path.exists(questions_dir):
                    os.makedirs(questions_dir)
                
                # Create sub-folders for sections 3 and 4
                qsec3_dir = os.path.join(questions_dir, 'qsec3')
                qsec4_dir = os.path.join(questions_dir, 'qsec4')
                
                if not os.path.exists(qsec3_dir):
                    os.makedirs(qsec3_dir)
                if not os.path.exists(qsec4_dir):
                    os.makedirs(qsec4_dir)
                
                # Save section 3 questions
                output_filename_qsec3 = f"{Path(transcript_path).stem}_Qsec3.txt"
                output_path_qsec3 = os.path.join(qsec3_dir, output_filename_qsec3)
                with open(output_path_qsec3, 'w', encoding='utf-8') as f:
                    f.write(section3)
                print(f"Processed section 3 saved to {output_path_qsec3}")
                
                # Save section 4 questions
                output_filename_qsec4 = f"{Path(transcript_path).stem}_Qsec4.txt"
                output_path_qsec4 = os.path.join(qsec4_dir, output_filename_qsec4)
                with open(output_path_qsec4, 'w', encoding='utf-8') as f:
                    f.write(section4)
                print(f"Processed section 4 saved to {output_path_qsec4}")
                
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