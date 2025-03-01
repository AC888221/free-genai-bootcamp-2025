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
        # Bootcamp Week 2: Format request for Titan embedding model
        request_body = {
            "inputText": question,
            "embeddingConfig": {
                "outputEmbeddingLength": 1536  # Bootcamp Week 2: Specify desired embedding length
            }
        }
        try:
            # Bootcamp Week 2: Use invoke_model with proper headers as per InvokeModel.md
            response = bedrock_client.invoke_model(
                modelId=embedding_model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body)
            )
            # Bootcamp Week 2: Parse streaming response body with error handling
            response_body = json.loads(response.get('body').read().decode())
            embedding = np.array(response_body.get('embedding', []), dtype='float32')
            if len(embedding) == 1536:
                embeddings.append(embedding)
            else:
                print(f"Unexpected embedding dimension: {len(embedding)}")
                embeddings.append(np.zeros(1536, dtype='float32'))
        except Exception as e:
            print(f"Error calling Bedrock API: {str(e)}")
            embeddings.append(np.zeros(1536, dtype='float32'))
    
    if not embeddings:
        print("Warning: No embeddings generated, returning zero matrix")
        return np.zeros((len(questions), 1536), dtype='float32')
    
    return np.array(embeddings)

# No need for process_sections or any question handling here

# ... existing vector store functions ...
