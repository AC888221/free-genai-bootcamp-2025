import boto3
import numpy as np
import faiss
import json
import pickle
import os
from pathlib import Path
from typing import List, Dict
import hashlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
                logging.warning(f"Unexpected embedding dimension: {len(embedding)}")
                embeddings.append(np.zeros(384, dtype='float32'))
        except Exception as e:
            logging.error(f"Error calling Bedrock API: {str(e)}")
            embeddings.append(np.zeros(384, dtype='float32'))
    
    if not embeddings:
        logging.warning("No embeddings generated, returning zero matrix")
        return np.zeros((len(questions), 384), dtype='float32')
    
    return np.array(embeddings)

def process_question_files(input_dir: str, embedding_model_id: str, section: str) -> Dict[str, Dict[str, np.ndarray]]:
    """Process question files in the specified directory and return their embeddings with metadata"""
    embeddings = {}
    input_directory = Path(input_dir)
    
    for file_path in input_directory.glob('*.txt'):
        with open(file_path, 'r', encoding='utf-8') as f:
            questions = f.read().split('\n')
            questions = [q for q in questions if q.strip()]  # Remove empty lines
            embeddings[file_path.stem] = {
                "section": section,
                "questions": questions,
                "embeddings": embed_questions(questions, embedding_model_id)
            }
    
    return embeddings

def save_embeddings(embeddings: Dict[str, Dict[str, np.ndarray]], output_dir: str):
    """Save embeddings to disk using FAISS and pickle"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    combined_embeddings = []
    combined_metadata = []
    existing_hashes = set()
    
    # Load existing metadata if it exists
    metadata_path = os.path.join(output_dir, 'vectors_metadata.pkl')
    if os.path.exists(metadata_path):
        with open(metadata_path, 'rb') as f:
            existing_metadata = pickle.load(f)
            for meta in existing_metadata:
                try:
                    question_hash = hashlib.md5(meta["question"].encode()).hexdigest()
                    existing_hashes.add(question_hash)
                except KeyError as e:
                    logging.error(f"KeyError: {e} in existing metadata: {meta}")
            combined_metadata.extend(existing_metadata)
    
    for name, data in embeddings.items():
        section = data["section"]
        questions = data["questions"]
        embedding = data["embeddings"]
        
        for i, question in enumerate(questions):
            question_hash = hashlib.md5(question.encode()).hexdigest()
            if question_hash not in existing_hashes:
                combined_embeddings.append(embedding[i])
                combined_metadata.append({"name": name, "section": section, "question": question})
                existing_hashes.add(question_hash)
    
    if combined_embeddings:
        combined_embeddings = np.vstack(combined_embeddings)
        
        index = faiss.IndexFlatL2(combined_embeddings.shape[1])
        index.add(combined_embeddings)
        faiss.write_index(index, os.path.join(output_dir, 'vectors.faiss'))
        
        with open(metadata_path, 'wb') as f:
            pickle.dump(combined_metadata, f)
        
        logging.info(f"Combined embeddings saved to {output_dir}")
    else:
        logging.info("No new embeddings to save.")

def load_embeddings(input_dir: str) -> Dict[str, Dict[str, np.ndarray]]:
    """Load embeddings from disk using FAISS and pickle"""
    embeddings = {}
    index = faiss.read_index(os.path.join(input_dir, 'vectors.faiss'))
    
    with open(os.path.join(input_dir, 'vectors_metadata.pkl'), 'rb') as f:
        metadata = pickle.load(f)
    
    for i, meta in enumerate(metadata):
        name = meta["name"]
        section = meta["section"]
        question = meta["question"]
        embedding = index.reconstruct(i)
        if name not in embeddings:
            embeddings[name] = {"section": section, "questions": [], "embeddings": []}
        embeddings[name]["questions"].append(question)
        embeddings[name]["embeddings"].append(embedding)
    
    for name in embeddings:
        embeddings[name]["embeddings"] = np.array(embeddings[name]["embeddings"])
    
    logging.info(f"Combined embeddings loaded from {input_dir}")
    
    return embeddings

if __name__ == "__main__":
    embedding_model_id = "amazon.titan-embed-image-v1"
    qsec3_dir = os.path.join(os.path.dirname(__file__), 'data', 'questions', 'qsec3')
    qsec4_dir = os.path.join(os.path.dirname(__file__), 'data', 'questions', 'qsec4')
    output_dir = os.path.join(os.path.dirname(__file__), 'data')
    
    # Process and save embeddings for section 3
    qsec3_embeddings = process_question_files(qsec3_dir, embedding_model_id, "HSK 2 Section 3")
    save_embeddings(qsec3_embeddings, output_dir)
    
    # Process and save embeddings for section 4
    qsec4_embeddings = process_question_files(qsec4_dir, embedding_model_id, "HSK 2 Section 4")
    save_embeddings(qsec4_embeddings, output_dir)
    
    # Example of loading embeddings
    loaded_embeddings = load_embeddings(output_dir)