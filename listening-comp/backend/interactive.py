import sys
import os

# Add the root directory of the project to the PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pickle
import faiss
import numpy as np
from backend.rag import load_embeddings_with_hsk2_data, find_top_n_similar, read_hsk2_data
from backend.chat import BedrockChat
from gtts import gTTS

# Load embeddings and metadata
def load_embeddings():
    with open('backend/data/vectors_metadata.pkl', 'rb') as f:
        metadata = pickle.load(f)
    index = faiss.read_index('backend/data/vectors.faiss')
    return index, metadata

# Process user prompts and predefined options
def process_prompt(prompt, index, metadata):
    # Generate embedding for the prompt
    embedding = np.random.rand(384)  # Replace with actual model output
    D, I = index.search(np.array([embedding]), k=5)
    results = [metadata[i] for i in I[0]]
    return results

# Generate and display question transcripts
def generate_transcript(question):
    return f"Question: {question['question']}"

# Play transcript as audio
def play_audio(text):
    tts = gTTS(text, lang='zh')
    tts.save("temp_audio.mp3")
    os.system("mpg321 temp_audio.mp3")

# Reveal correct answer
def reveal_answer(question):
    answer = question.get('answer', 'No answer available')
    return f"Correct Answer: {answer}"

# Main function to run the backend independently
def run_interactive_backend():
    # Load embeddings and metadata
    index, metadata = load_embeddings()
    
    while True:
        prompt = input("Enter your question or type '/exit' to quit: ")
        if prompt.lower() == '/exit':
            break
        
        results = process_prompt(prompt, index, metadata)
        for result in results:
            print(generate_transcript(result))
            play_audio_option = input("Do you want to play the audio? (y/n): ")
            if play_audio_option.lower() == 'y':
                play_audio(result['question'])
            reveal_answer_option = input("Do you want to reveal the answer? (y/n): ")
            if reveal_answer_option.lower() == 'y':
                print(reveal_answer(result))

if __name__ == "__main__":
    run_interactive_backend()