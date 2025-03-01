import streamlit as st
from typing import Dict
import json
from collections import Counter
import re
import sys
import os
import boto3
import numpy as np
import pickle
import faiss

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.get_transcript import YouTubeTranscriptDownloader
from backend.chat import BedrockChat
from backend.structured_data import HSK2TranscriptProcessor
from backend.vector_store import embed_questions, process_question_files, save_embeddings
from sklearn.metrics.pairwise import cosine_similarity

# Page config
st.set_page_config(
    page_title="Putonghua Learning Assistant", # Bootcamp Week 2: Adapt to Putonghua
    page_icon="assets/china_flag.png", # Bootcamp Week 2: Use image instead of emoji
    layout="wide"
)

# Initialize session state
if 'transcript' not in st.session_state:
    st.session_state.transcript = None
if 'messages' not in st.session_state:
    st.session_state.messages = []

def render_header():
    """Render the header section"""
    st.title("🇨🇳 Putonghua Learning Assistant") # Bootcamp Week 2: Adapt to Putonghua
    st.markdown("""
    Transform YouTube transcripts into interactive Putonghua learning experiences.  
    [Featuring: **Base LLM Capabilities**, **RAG (Retrieval Augmented Generation)**, **Amazon Bedrock Integration**, and **Agent-based Learning Systems**.]
    """) # Bootcamp Week 2: Takes up less space

def render_sidebar():
    """Render the sidebar with component selection"""
    with st.sidebar:
        st.header("Development Stages")
        
        # Main component selection
        selected_stage = st.radio(
            "Select Stage:",
            [
                "1. Chat with Nova",
                "2. Raw Transcript",
                "3. Structured Data",
                "4. RAG Implementation",
                "5. Interactive Learning"
            ]
        )
        
        # Stage descriptions
        stage_info = {
            "1. Chat with Nova": """
            **Current Focus:**
            - Basic Putonghua learning
            - Understanding LLM capabilities
            - Identifying limitations
            """,
            
            "2. Raw Transcript": """
            **Current Focus:**
            - YouTube transcript download
            - Raw text visualization
            - Initial data examination
            """,
            
            "3. Structured Data": """
            **Current Focus:**
            - Text cleaning
            - Dialogue extraction
            - Data structuring
            """,
            
            "4. RAG Implementation": """
            **Current Focus:**
            - Bedrock embeddings
            - Vector storage
            - Context retrieval
            """,
            
            "5. Interactive Learning": """
            **Current Focus:**
            - Scenario generation
            - Audio synthesis
            - Interactive practice
            """
        } # Bootcamp Week 2: Adapt to Putonghua
        
        st.markdown("---")
        st.markdown(stage_info[selected_stage])
        
        return selected_stage

def render_chat_stage():
    """Render an improved chat interface"""
    st.header("Chat with Nova")

    # Initialize BedrockChat instance if not in session state
    if 'bedrock_chat' not in st.session_state:
        st.session_state.bedrock_chat = BedrockChat()

    # Introduction text
    st.markdown("""
    Start by exploring Nova's base Putonghua capabilities. Try asking questions about Chinese grammar, 
    vocabulary, or cultural aspects.
    """) # Bootcamp Week 2: Adapt to Putonghua

    # Initialize chat history if not exists
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🧑‍💻" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])

    # Chat input area
    if prompt := st.chat_input("Ask about the Putonghua language ..."): # Bootcamp Week 2: Adapt to Putonghua
        # Process the user input
        process_message(prompt)

    # Example questions in sidebar
    with st.sidebar:
        st.markdown("### Try These Examples")
        example_questions = [
            "How do I say 'Where is the train station?' in Putonghua?",
            "Explain the difference between 吗 and 呢",
            "What's the polite form of 吃?",
            "How do I count objects in Putonghua?",
            "What's the difference between 你好 and 您好?",
            "How do I ask for directions politely?"
        ]
        
        for q in example_questions:
            st.markdown(f'<a href="javascript:void(0)" style="color: blue; text-decoration: underline;">{q}</a>', unsafe_allow_html=True)
            if st.button("Ask", key=q, use_container_width=True, type="secondary"):
                # Process the example question
                process_message(q)
                st.rerun()

    # Add a clear chat button
    if st.session_state.messages:
        if st.button("Clear Chat", type="primary"):
            st.session_state.messages = []
            st.rerun()

def process_message(message: str):
    """Process a message and generate a response"""
    # Add user message to state and display
    st.session_state.messages.append({"role": "user", "content": message})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(message)

    # Generate and display assistant's response
    with st.chat_message("assistant", avatar="🤖"):
        response = st.session_state.bedrock_chat.generate_response(message)
        if response:
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# Bootcamp Week 2: Moved and adapted function to download the transcript of a YouTube video in Simplified Chinese and store it in the session state
def download_transcript(video_url):
    """Download the transcript for the given video URL."""
    # Initialize the downloader with Simplified Chinese as the target language
    downloader = YouTubeTranscriptDownloader(languages=["zh-Hans"])
    
    # Retrieve the transcript for the specified video URL
    transcript = downloader.get_transcript(video_url)
    
    if transcript:
        # Extract video ID
        video_id = downloader.extract_video_id(video_url)
        
        # Save the transcript to the backend/data/transcripts/ directory
        if downloader.save_transcript(transcript, video_id):
            # Store the video ID and transcript in the session state, overwriting any existing data
            st.session_state.transcript_data = {
                'video_id': video_id,
                'transcript': "\n".join([entry['text'] for entry in transcript])
            }
            st.success("Transcript downloaded and saved successfully!")
        else:
            st.error("Failed to save transcript.")
    else:
        # Bootcamp Week 2: Clear the transcript in case of failure
        st.session_state.transcript_data = None  # Clear the transcript data
        st.error("Failed to download transcript.")

def count_characters(text):
    """Count Simplified Chinese-specific and total characters in text"""
    if not text:
        return 0, 0
        
    def is_chinese(char):
        return '\u4e00' <= char <= '\u9fff'  # Simplified Chinese characters range
    
    cn_chars = sum(1 for char in text if is_chinese(char))
    return cn_chars, len(text)

def render_transcript_stage():
    """Render the raw transcript stage"""
    st.header("Raw Transcript Processing")
    
    # URL input
    url = st.text_input(
        "YouTube URL",
        placeholder="Enter a Putonghua HSK 2 Practice Test YouTube URL" # Bootcamp Week 2: Adapt to Putonghua
    )
    
    # Download button and processing
    if url:
        if st.button("Download Transcript"):
            download_transcript(url)

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Raw Transcript")
        if 'transcript_data' in st.session_state and st.session_state.transcript_data:
            st.text_area(
                label="Raw text",
                value=st.session_state.transcript_data['transcript'],
                height=400,
                disabled=True
            )
        else:
            st.info("No transcript loaded")
    
    with col2:
        st.subheader("Transcript Stats")
        if 'transcript_data' in st.session_state and st.session_state.transcript_data:
            # Calculate stats
            cn_chars, total_chars = count_characters(st.session_state.transcript_data['transcript'])
            total_lines = len(st.session_state.transcript_data['transcript'].split('\n'))
            
            # Display stats
            st.metric("Total Characters", total_chars)
            st.metric("Simplified Chinese Characters", cn_chars)
            st.metric("Total Lines", total_lines)
        else:
            st.info("Load a transcript to see statistics")

def render_structured_stage():
    """Render the structured data stage"""
    st.header("Structured Data Processing")
    
    st.subheader("Question Extraction")
    st.info("Question extraction will be implemented here")
  
    # Check if transcript data is available in session state
    if 'transcript_data' in st.session_state:
        transcript_data = st.session_state.transcript_data
        transcript = transcript_data['transcript']
        video_id = transcript_data['video_id']
        
        # Initialize the processor
        processor = HSK2TranscriptProcessor()
        
        # Generate prompt
        prompt = processor._generate_prompt(transcript)
        
        # Process with Bedrock
        processed_text = processor._process_with_bedrock(prompt)
        
        if processed_text:
            st.success("Transcript processed successfully!")
            st.text_area("Processed Transcript", processed_text, height=300)
            
            # Save each question individually in their respective section folders
            lines = processed_text.split('\n')
            questions = [line for line in lines if line.strip() and "：" in line]
            
            output_dir = os.path.join(os.path.dirname(__file__), '..', 'backend', 'data')
            session_questions = []
            for i, question in enumerate(questions, start=1):
                # Skip sections 1 and 2
                if i <= 20:
                    continue
                
                section = 'qsec3' if 21 <= i <= 30 else 'qsec4'
                section_dir = os.path.join(output_dir, 'questions', section)
                if not os.path.exists(section_dir):
                    os.makedirs(section_dir)
                
                question_id = processor._generate_id(video_id, i)
                question_path = os.path.join(section_dir, f"{question_id}.txt")
                with open(question_path, 'w', encoding='utf-8') as f:
                    f.write(question)
                st.info(f"Saved question to {question_path}")
                
                # Store question in session state
                session_questions.append({
                    'question_id': question_id,
                    'question': question,
                    'section': section
                })
            
            # Save questions to session state
            st.session_state.processed_questions = session_questions
            
            # Embed questions
            embedding_model_id = "amazon.titan-embed-image-v1"  # Use the embedding model ID from vector_store.py
            question_texts = [q['question'] for q in session_questions]
            embeddings = embed_questions(question_texts, embedding_model_id)
            
            # Ensure embeddings are correctly generated
            if embeddings.size == 0:
                st.error("Failed to generate embeddings.")
                return
            
            # Print the shape of the embeddings to debug
            print("Embeddings shape:", embeddings.shape)
            
            # Prepare embeddings and metadata for saving
            embeddings_dict = {}
            for q, emb in zip(session_questions, embeddings):
                if q['section'] not in embeddings_dict:
                    embeddings_dict[q['section']] = {
                        'section': q['section'],
                        'questions': [],
                        'embeddings': []
                    }
                embeddings_dict[q['section']]['questions'].append(q['question'])
                embeddings_dict[q['section']]['embeddings'].append(emb)
            
            # Save embeddings using the save_embeddings function from vector_store.py
            save_embeddings(embeddings_dict, output_dir)
            
            st.success("Questions embedded and saved successfully!")
        else:
            st.error("Failed to process transcript.")
    else:
        st.warning("No transcript data available. Please download a transcript first.")

def load_embeddings(folder_path):
    """Load embeddings from the specified folder"""
    embeddings = {}
    current_dir = os.getcwd()
    full_path = os.path.abspath(os.path.join(current_dir, folder_path))
    
    if not os.path.exists(full_path):
        st.error(f"Directory not found: {full_path}")
        return embeddings
    
    try:
        for filename in os.listdir(full_path):
            if filename.endswith(".pkl"):
                with open(os.path.join(full_path, filename), 'rb') as file:
                    try:
                        embeddings[filename] = pickle.load(file)
                    except pickle.UnpicklingError:
                        st.error(f"Error unpickling file: {filename}")
    except FileNotFoundError:
        st.error(f"Directory not found: {full_path}")
    except Exception as e:
        st.error(f"An error occurred: {e}")
    
    return embeddings

def find_top_n_similar(query_embedding, embeddings, n=3):
    """Find the top n most similar embeddings to the query"""
    similarities = []
    
    for context, embedding in embeddings.items():
        similarity = cosine_similarity([query_embedding], [embedding])[0][0]
        similarities.append((context, similarity))
    
    # Sort by similarity and return the top n
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_n_similar = [context for context, _ in similarities[:n]]
    
    return top_n_similar

def process_rag_message(message: str):
    """Process a message and generate a response for the RAG stage"""
    # Add user message to state and display
    st.session_state.messages.append({"role": "user", "content": message})

    # Load embeddings from both folders
    embeddings_qsec3 = load_embeddings('backend/data/embeddings/embed_qsec3')
    embeddings_qsec4 = load_embeddings('backend/data/embeddings/embed_qsec4')

    # Generate query embedding (this is a placeholder, replace with actual embedding generation)
    query_embedding = np.random.rand(768)  # Example: random embedding, replace with actual model output

    # Retrieve the top 3 most similar contexts
    retrieved_contexts_qsec3 = find_top_n_similar(query_embedding, embeddings_qsec3, n=3)
    retrieved_contexts_qsec4 = find_top_n_similar(query_embedding, embeddings_qsec4, n=3)
    retrieved_contexts = retrieved_contexts_qsec3 + retrieved_contexts_qsec4
    st.session_state.retrieved_contexts = retrieved_contexts

    # Generate response using BedrockChat
    response = st.session_state.bedrock_chat.generate_response(message)
    st.session_state.generated_response = response

def render_rag_stage():
    """Render the RAG implementation stage"""
    st.header("RAG System")
    
    # Initialize BedrockChat instance if not in session state
    if 'bedrock_chat' not in st.session_state:
        st.session_state.bedrock_chat = BedrockChat()

    # Query input field
    query = st.text_input(
        "Test Query",
        placeholder="Enter a question about Japanese...",
        key="query_input"
    )
    
    # Process the user input if any
    if query:
        process_rag_message(query)

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Retrieved Context")
        # Display retrieved contexts or indicate none found
        if 'retrieved_contexts' in st.session_state and st.session_state.retrieved_contexts:
            for context in st.session_state.retrieved_contexts:
                st.info(context)
        else:
            st.info("No additional context found.")
        
    with col2:
        st.subheader("Generated Response")
        # Display generated response with blue background
        if 'generated_response' in st.session_state:
            st.markdown(
                f"<div style='background-color: #e0f7fa; padding: 10px; border-radius: 5px;'>{st.session_state.generated_response}</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<div style='background-color: #e0f7fa; padding: 10px; border-radius: 5px;'>Generated response will appear here</div>",
                unsafe_allow_html=True
            )

# Example usage
def main():
    render_header()
    selected_stage = render_sidebar()
    
    # Render appropriate stage
    if selected_stage == "1. Chat with Nova":
        render_chat_stage()
    elif selected_stage == "2. Raw Transcript":
        render_transcript_stage()
    elif selected_stage == "3. Structured Data":
        render_structured_stage()
    elif selected_stage == "4. RAG Implementation":
        render_rag_stage()
    elif selected_stage == "5. Interactive Learning":
        render_interactive_stage()
    
    # Debug section at the bottom
    with st.expander("Debug Information"):
        st.json({
            "selected_stage": selected_stage,
            "transcript_loaded": st.session_state.transcript is not None,
            "chat_messages": len(st.session_state.messages)
        })

if __name__ == "__main__":
    main()