import boto3
from typing import Optional, List, Dict
import os
from pathlib import Path
import hashlib
import faiss
import numpy as np
import pickle

class HSK2TranscriptProcessor:
    def __init__(self, model_id: str = "amazon.nova-micro-v1:0"):
        """Initialize Bedrock client and FAISS for transcript processing"""
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
                
                # Process section 3
                section3_questions = section3.split('\n')
                section3_vectors = self._embed_questions(section3_questions)
                index_sec3 = faiss.IndexFlatL2(768)
                index_sec3.add(section3_vectors)
                metadata_sec3 = [{
                    "source": Path(transcript_path).stem,
                    "section": "3",
                    "question_number": i + 21
                } for i in range(len(section3_questions))]
                
                # Process section 4
                section4_questions = section4.split('\n')
                section4_vectors = self._embed_questions(section4_questions)
                index_sec4 = faiss.IndexFlatL2(768)
                index_sec4.add(section4_vectors)
                metadata_sec4 = [{
                    "source": Path(transcript_path).stem,
                    "section": "4",
                    "question_number": i + 31
                } for i in range(len(section4_questions))]
                
                # Save to files as before
                output_filename_sec3 = f"{Path(transcript_path).stem}_Qsec3.txt"
                output_path_sec3 = os.path.join(output_dir, output_filename_sec3)
                with open(output_path_sec3, 'w', encoding='utf-8') as f:
                    f.write(section3)
                print(f"Processed section 3 saved to {output_path_sec3}")
                
                output_filename_sec4 = f"{Path(transcript_path).stem}_Qsec4.txt"
                output_path_sec4 = os.path.join(output_dir, output_filename_sec4)
                with open(output_path_sec4, 'w', encoding='utf-8') as f:
                    f.write(section4)
                print(f"Processed section 4 saved to {output_path_sec4}")
                
                # Save indices and metadata
                self.save_indices_and_metadata(output_dir, Path(transcript_path).stem, index_sec3, metadata_sec3, index_sec4, metadata_sec4)
                
                return processed_text
            else:
                print(f"Failed to process transcript {transcript_path}")
                return None
        except Exception as e:
            print(f"Error processing transcript {transcript_path}: {str(e)}")
            return None

    def _embed_questions(self, questions: List[str]) -> np.ndarray:
        """Embed questions into vectors (dummy implementation)"""
        # Replace this with actual embedding logic
        return np.random.rand(len(questions), 768).astype('float32')

    def query_similar_questions(self, query: str, section: int, limit: int = 5) -> List[Dict]:
        """Query similar questions from a specific section"""
        query_vector = self._embed_questions([query])[0]
        index = self.index_sec3 if section == 3 else self.index_sec4
        metadata = self.metadata_sec3 if section == 3 else self.metadata_sec4
        
        distances, indices = index.search(np.array([query_vector]), limit)
        
        # Format results
        formatted_results = []
        for i, idx in enumerate(indices[0]):
            formatted_results.append({
                'question': metadata[idx]['question'],
                'metadata': metadata[idx],
                'similarity_score': distances[0][i]
            })
        
        return formatted_results

    def process_directory(self, input_dir: str, output_dir: str) -> Dict[str, Optional[str]]:
        """Process all transcript files in a directory"""
        results = {}
        input_directory = Path(input_dir)
        
        for file_path in input_directory.glob('*.txt'):
            results[file_path.name] = self.process_transcript(str(file_path), output_dir)
            
        return results

    def save_indices_and_metadata(self, output_dir: str, transcript_name: str, index_sec3, metadata_sec3, index_sec4, metadata_sec4):
        """Save FAISS indices and metadata to disk"""
        vectorstore_sec3 = os.path.join(output_dir, 'vectorstore_sec3')
        vectorstore_sec4 = os.path.join(output_dir, 'vectorstore_sec4')
        
        if not os.path.exists(vectorstore_sec3):
            os.makedirs(vectorstore_sec3)
        if not os.path.exists(vectorstore_sec4):
            os.makedirs(vectorstore_sec4)
        
        faiss.write_index(index_sec3, os.path.join(vectorstore_sec3, f'index_sec3_{transcript_name}.faiss'))
        faiss.write_index(index_sec4, os.path.join(vectorstore_sec4, f'index_sec4_{transcript_name}.faiss'))
        
        with open(os.path.join(vectorstore_sec3, f'metadata_sec3_{transcript_name}.pkl'), 'wb') as f:
            pickle.dump(metadata_sec3, f)
        with open(os.path.join(vectorstore_sec4, f'metadata_sec4_{transcript_name}.pkl'), 'wb') as f:
            pickle.dump(metadata_sec4, f)
        print(f"Indices and metadata for {transcript_name} saved to {output_dir}")

    def load_indices_and_metadata(self, input_dir: str, transcript_name: str):
        """Load FAISS indices and metadata from disk"""
        vectorstore_sec3 = os.path.join(input_dir, 'vectorstore_sec3')
        vectorstore_sec4 = os.path.join(input_dir, 'vectorstore_sec4')
        
        index_sec3 = faiss.read_index(os.path.join(vectorstore_sec3, f'index_sec3_{transcript_name}.faiss'))
        index_sec4 = faiss.read_index(os.path.join(vectorstore_sec4, f'index_sec4_{transcript_name}.faiss'))
        
        with open(os.path.join(vectorstore_sec3, f'metadata_sec3_{transcript_name}.pkl'), 'rb') as f:
            metadata_sec3 = pickle.load(f)
        with open(os.path.join(vectorstore_sec4, f'metadata_sec4_{transcript_name}.pkl'), 'rb') as f:
            metadata_sec4 = pickle.load(f)
        
        print(f"Indices and metadata for {transcript_name} loaded from {input_dir}")
        return index_sec3, metadata_sec3, index_sec4, metadata_sec4

if __name__ == "__main__":
    # Example usage
    processor = HSK2TranscriptProcessor()
    transcripts_dir = os.path.join(os.path.dirname(__file__), 'data', 'transcripts')
    questions_dir = os.path.join(os.path.dirname(__file__), 'data')
    
    if not os.path.exists(questions_dir):
        os.makedirs(questions_dir)
    
    results = processor.process_directory(transcripts_dir, questions_dir)
    
    for filename, processed_text in results.items():
        if processed_text:
            print(f"\nProcessed {filename}:")
            print(processed_text)
    
    # Save indices and metadata for each transcript
    for filename in results.keys():
        transcript_name = Path(filename).stem
        index_sec3, metadata_sec3, index_sec4, metadata_sec4 = processor.load_indices_and_metadata(questions_dir, transcript_name)
        processor.save_indices_and_metadata(questions_dir, transcript_name, index_sec3, metadata_sec3, index_sec4, metadata_sec4)