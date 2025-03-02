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
    def __init__(self, model_id: str = MODEL_ID, system_prompt: str = ""):
        """Initialize Bedrock chat client with an optional system prompt"""
        self.bedrock_client = boto3.client('bedrock-runtime', region_name="us-east-1")
        self.model_id = model_id
        self.system_prompt = system_prompt

    def generate_response(self, message: str, inference_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Generate a response using Amazon Bedrock"""
        if inference_config is None:
            inference_config = {"temperature": 0.7}

        combined_message = self.system_prompt + "\n\n" + message

        messages = [{
            "role": "user",
            "content": [{"text": combined_message}]
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

def read_hsk2_data(file_path):
    """Read the HSK2 data from the markdown file"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def load_embeddings_with_hsk2_data(folder_path, hsk2_data):
    """Load embeddings from the specified folder and include HSK2 data"""
    embeddings = load_embeddings(folder_path)
    hsk2_embedding = np.random.rand(384)  # Example: random embedding, replace with actual embedding for HSK2 data
    embeddings['HSK2_data'] = hsk2_embedding
    return embeddings

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
    hsk2_data = read_hsk2_data('backend/data/HSK2_data.md')
    embeddings_transcripts = load_embeddings_with_hsk2_data('backend/data', hsk2_data)
    system_prompt = "You are an expert in HSK (Hanyu Shuiping Kaoshi) listening tests. You will be given the examples of HSK 2 listening test audio transcripts from sections 3 and 4 that best match the user's own input. You must produce a new HSK 2 listen test audio transcript. You must add 4 suitable Multiple Choice Question answer choices, one of which will be a good match for the context of the listening test audio transcript you produce. You must only reply in simplified Chinese."
    chat = BedrockChat(system_prompt=system_prompt)

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