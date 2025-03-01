import boto3
import numpy as np
import faiss
import json
import pickle
import os
from pathlib import Path
from typing import List, Dict

def embed_questions(questions: List[str], embedding_model_id: str) -> np.ndarray:
    """Embed questions into vectors using Amazon Bedrock"""
    embeddings = []
    bedrock_client = boto3.client('bedrock-runtime', region_name="us-east-1")
    for question in questions:
        request_body = {
            "inputText": question,
            "embeddingConfig": {
                "outputEmbeddingLength": 384  # Specify desired embedding length
            }
        }
        try:
            response = bedrock_client.invoke_model(
                modelId=embedding_model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body)
            )
            response_body = json.loads(response.get('body').read().decode())
            embedding = np.array(response_body.get('embedding', []), dtype='float32')
            if len(embedding) == 384:
                embeddings.append(embedding)
            else:
                print(f"Unexpected embedding dimension: {len(embedding)}")
                embeddings.append(np.zeros(384, dtype='float32'))
        except Exception as e:
            print(f"Error calling Bedrock API: {str(e)}")
            embeddings.append(np.zeros(384, dtype='float32'))
    
    if not embeddings:
        print("Warning: No embeddings generated, returning zero matrix")
        return np.zeros((len(questions), 384), dtype='float32')
    
    return np.array(embeddings)

def process_question_files(input_dir: str, embedding_model_id: str) -> Dict[str, np.ndarray]:
    """Process question files in the specified directory and return their embeddings"""
    embeddings = {}
    input_directory = Path(input_dir)
    
    for file_path in input_directory.glob('*.txt'):
        with open(file_path, 'r', encoding='utf-8') as f:
            questions = f.read().split('\n')
            questions = [q for q in questions if q.strip()]  # Remove empty lines
            embeddings[file_path.stem] = embed_questions(questions, embedding_model_id)
    
    return embeddings

def save_embeddings(embeddings: Dict[str, np.ndarray], output_dir: str):
    """Save embeddings to disk using FAISS and pickle"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for name, embedding in embeddings.items():
        index = faiss.IndexFlatL2(embedding.shape[1])
        index.add(embedding)
        faiss.write_index(index, os.path.join(output_dir, f'{name}.faiss'))
        
        with open(os.path.join(output_dir, f'{name}_metadata.pkl'), 'wb') as f:
            pickle.dump(embedding, f)
        print(f"Embeddings for {name} saved to {output_dir}")

def load_embeddings(input_dir: str) -> Dict[str, np.ndarray]:
    """Load embeddings from disk using FAISS and pickle"""
    embeddings = {}
    input_directory = Path(input_dir)
    
    for file_path in input_directory.glob('*.faiss'):
        name = file_path.stem
        index = faiss.read_index(str(file_path))
        with open(input_directory / f'{name}_metadata.pkl', 'rb') as f:
            metadata = pickle.load(f)
        embeddings[name] = metadata
        print(f"Embeddings for {name} loaded from {input_dir}")
    
    return embeddings

if __name__ == "__main__":
    embedding_model_id = "amazon.titan-embed-image-v1"
    qsec3_dir = os.path.join(os.path.dirname(__file__), 'data', 'questions', 'qsec3')
    qsec4_dir = os.path.join(os.path.dirname(__file__), 'data', 'questions', 'qsec4')
    output_dir_qsec3 = os.path.join(os.path.dirname(__file__), 'data', 'embeddings', 'embed_qsec3')
    output_dir_qsec4 = os.path.join(os.path.dirname(__file__), 'data', 'embeddings', 'embed_qsec4')
    
    # Process and save embeddings for section 3
    qsec3_embeddings = process_question_files(qsec3_dir, embedding_model_id)
    save_embeddings(qsec3_embeddings, output_dir_qsec3)
    
    # Process and save embeddings for section 4
    qsec4_embeddings = process_question_files(qsec4_dir, embedding_model_id)
    save_embeddings(qsec4_embeddings, output_dir_qsec4)
    
    # Example of loading embeddings
    loaded_embeddings_qsec3 = load_embeddings(output_dir_qsec3)
    loaded_embeddings_qsec4 = load_embeddings(output_dir_qsec4)