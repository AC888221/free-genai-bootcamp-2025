import faiss
import numpy as np
import os
import pickle
from typing import List, Dict

# Function to load embeddings from disk using FAISS and pickle
def load_embeddings(input_dir: str) -> Dict[str, np.ndarray]:
    embeddings = {}
    for file_name in os.listdir(input_dir):
        if file_name.endswith('.faiss'):
            name = file_name.split('.')[0]
            index = faiss.read_index(os.path.join(input_dir, file_name))
            with open(os.path.join(input_dir, f'{name}_metadata.pkl'), 'rb') as f:
                metadata = pickle.load(f)
            embeddings[name] = (index, metadata)
            print(f"Embeddings for {name} loaded from {input_dir}")
    return embeddings

# Function to embed query text using Amazon Bedrock
def embed_query(query_text: str, embedding_model_id: str) -> np.ndarray:
    """Embed query text into a vector using Amazon Bedrock"""
    bedrock_client = boto3.client('bedrock-runtime', region_name="us-east-1")
    request_body = {
        "inputText": query_text,
        "embeddingConfig": {
            "outputEmbeddingLength": 384  # Specify desired embedding length
        }
    }
    response = bedrock_client.invoke_model(
        modelId=embedding_model_id,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(request_body)
    )
    response_body = json.loads(response.get('body').read().decode())
    embedding = np.array(response_body.get('embedding', []), dtype='float32')
    return embedding

# Function to query the embeddings
def query_embeddings(query_text: str, embeddings: Dict[str, np.ndarray], embedding_model_id: str, n_results=2) -> Dict[str, List[str]]:
    # Convert query text to embedding
    query_embedding = embed_query(query_text, embedding_model_id)
    
    results = {}
    for name, (index, metadata) in embeddings.items():
        D, I = index.search(np.array([query_embedding]), n_results)
        results[name] = [metadata[i] for i in I[0]]
    
    return results

# Example usage
if __name__ == "__main__":
    embedding_model_id = "amazon.titan-embed-image-v1"
    embeddings_dir = os.path.join(os.path.dirname(__file__), 'data', 'embeddings', 'embed_qsec3')
    
    # Load embeddings
    embeddings = load_embeddings(embeddings_dir)
    
    # Query the embeddings
    query_text = "This is a query document"
    results = query_embeddings(query_text, embeddings, embedding_model_id)
    print(results)