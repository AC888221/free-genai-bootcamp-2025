import os
import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import faiss
import boto3
from typing import Optional, Dict, Any

# Model ID
MODEL_ID = "amazon.nova-micro-v1:0"

class BedrockChat:
    def __init__(self, model_id: str = MODEL_ID):
        """Initialize Bedrock chat client"""
        self.bedrock_client = boto3.client('bedrock-runtime', region_name="us-east-1")
        self.model_id = model_id

    def generate_response(self, message: str, inference_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Generate a response using Amazon Bedrock"""
        if inference_config is None:
            inference_config = {"temperature": 0.7}

        messages = [{
            "role": "user",
            "content": [{"text": message}]
        }]

        try:
            response = self.bedrock_client.converse(
                modelId=self.model_id,
                messages=messages,
                inferenceConfig=inference_config
            )
            return response['output']['message']['content'][0]['text']
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return None

def replace_nan_with_mean(embedding, default_value=0.0):
    """Replace NaN values in the embedding with the mean of non-NaN values or a default value if mean is problematic"""
    if np.isnan(embedding).any():
        nan_mask = np.isnan(embedding)
        
        # Normalize the values
        max_value = np.nanmax(np.abs(embedding))
        if max_value == 0 or np.isnan(max_value):
            max_value = 1  # Prevent division by zero
        normalized_embedding = embedding / max_value
        
        # Calculate the mean of the normalized values
        normalized_mean = np.nanmean(normalized_embedding.astype(np.float64))
        
        # Recalculate the unnormalized mean
        unnormalized_mean = normalized_mean * max_value
        
        if np.isinf(unnormalized_mean) or np.isnan(unnormalized_mean):
            print(f"Mean value is problematic (inf or NaN), replacing NaN with default value: {default_value}")
            embedding[nan_mask] = default_value
        else:
            embedding[nan_mask] = unnormalized_mean
            print(f"Replaced NaN values with mean: {unnormalized_mean}")
    return embedding

def load_embeddings(folder_path):
    """Load embeddings from the specified folder"""
    embeddings = {}
    current_dir = os.getcwd()
    full_path = os.path.abspath(os.path.join(current_dir, folder_path))
    
    if not os.path.exists(full_path):
        print(f"Directory not found: {full_path}")
        return embeddings
    
    try:
        index = faiss.read_index(os.path.join(full_path, 'vectors.faiss'))
        with open(os.path.join(full_path, 'vectors_metadata.pkl'), 'rb') as file:
            try:
                metadata = pickle.load(file)
                
                if isinstance(metadata, list):
                    for i, item in enumerate(metadata):
                        if isinstance(item, dict) and 'name' in item:
                            embedding = index.reconstruct(i)
                            embedding = replace_nan_with_mean(embedding)  # Replace NaN values with mean
                            embeddings[item['name']] = embedding
                        else:
                            print(f"Unexpected data format for item {i} in vectors_metadata.pkl")
                else:
                    print(f"Unexpected data format in vectors_metadata.pkl")
            except pickle.UnpicklingError:
                print(f"Error unpickling file: vectors_metadata.pkl")
    except FileNotFoundError:
        print(f"File not found: vectors.faiss")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return embeddings

def find_top_n_similar(query_embedding, embeddings, n=3):
    """Find the top n most similar embeddings to the query"""
    similarities = []
    
    for context, embedding in embeddings.items():
        similarity = cosine_similarity([query_embedding], [embedding])[0][0]
        similarities.append((context, similarity))
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_n_similar = [context for context, _ in similarities[:n]]
    
    return top_n_similar

def process_rag_message(message, embeddings, chat):
    """Process a message and generate a response for the RAG stage"""
    query_embedding = np.random.rand(384)  # Example: random embedding, replace with actual model output

    retrieved_contexts = find_top_n_similar(query_embedding, embeddings, n=3)
    
    response = chat.generate_response(message)
    
    return retrieved_contexts, response

def main():
    embeddings_transcripts = load_embeddings('backend/data')
    chat = BedrockChat()

    while True:
        user_input = input("You: ")
        if user_input.lower() == '/exit':
            break
        
        retrieved_contexts, response = process_rag_message(user_input, embeddings_transcripts, chat)
        
        print("Retrieved Contexts:")
        for context in retrieved_contexts:
            print(context)
        
        print("\nGenerated Response:")
        print(response)

if __name__ == "__main__":
    main()