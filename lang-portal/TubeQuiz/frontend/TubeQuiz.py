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
from datetime import datetime
import subprocess
import logging  # Import the logging module
import faulthandler
faulthandler.enable()
from sklearn.metrics.pairwise import cosine_similarity

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.get_transcript import YouTubeTranscriptDownloader
from backend.chat import BedrockChat
from backend.structured_data import HSK2TranscriptProcessor
from backend.vector_store import embed_questions, process_question_files, save_embeddings
from backend.rag import load_embeddings_with_hsk2_data, find_top_n_similar, read_hsk2_data
from backend.interactive import replace_nan_with_mean, process_rag_message
from backend.tts import process_text_files


# Page config
st.set_page_config(
    page_title="TubeQuiz", # Bootcamp Week 2: Adapt to Putonghua
    page_icon=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "cn.png"),
    layout="wide"
)

# Initialize session state
if 'transcript' not in st.session_state:
    st.session_state.transcript = None
if 'messages' not in st.session_state:
    st.session_state.messages = []

def render_header():
    """Render the header section"""
    # Create a container for the header with custom styling
    with st.container():
        # Get the path to the assets directory (one level up from frontend)
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
        flag_path = os.path.join(assets_dir, "cn.png")
        
        # Create columns with specific pixel widths and vertical alignment using CSS
        st.markdown(
            """
            <style>
            [data-testid="column"]:nth-of-type(1) {
                width: 220px !important;
                flex: none !important;
                display: flex !important;
                align-items: center !important;
                padding-right: 0px !important;
            }
            [data-testid="column"]:nth-of-type(2) {
                padding-left: 0px !important;
            }
            .header-text {
                margin-top: 0;
                margin-bottom: 0;
                padding-top: 0;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if os.path.exists(flag_path):
                st.image(flag_path, width=200)
            else:
                st.write("🇨🇳")
        with col2:
            st.markdown('<h1 class="header-text">TubeQuiz</h1>', unsafe_allow_html=True)
            st.markdown(
                '<div class="header-text">Transform YouTube transcripts into interactive Putonghua learning experiences.<br>'
                '[Featuring: <b>Base LLM Capabilities</b>, <b>RAG (Retrieval Augmented Generation)</b>, '
                '<b>Amazon Bedrock Integration</b>, and <b>Agent-based Learning Systems</b>.]</div>',
                unsafe_allow_html=True
            )

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
                "5. Interactive Learning",
                "6. Interactive Response Audio"  # New stage added
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
            - Question extraction
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
            - Interactive practice
            """,

            "6. Interactive Response Audio": """
            - Audio response generation
            - Audio file management
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

def render_rag_stage():
    """Render the RAG implementation stage"""
    st.header("RAG System")
    
    if 'bedrock_chat' not in st.session_state:
        st.session_state.bedrock_chat = BedrockChat()
    
    query = st.text_input(
        "Test Query",
        placeholder="Ask about Section 3 and 4 of the HSK 2 Putonghua Exam.",
        key="query_input"
    )
    
    if query:
        system_prompt = "You are an expert in HSK (Hanyu Shuiping Kaoshi) listening tests. Provide detailed and helpful responses to questions about HSK listening exams. You will be given the examples of HSK 2 listening test audio transcripts from sections 3 and 4 that best match the user's own input. You must produce a new HSK 2 listen test audio transcript. You must add 4 suitable Multiple Choice Question answer choices, one of which must be a noticeably better match than the others for the context of the listening test audio transcript you produce. You must only reply in simplified Chinese."
        hsk2_data = read_hsk2_data('backend/data/HSK2_data.md')
        embeddings_transcripts = load_embeddings_with_hsk2_data('backend/data', hsk2_data)
        combined_message = system_prompt + "\n\n" + query
        retrieved_contexts, response = process_rag_message(combined_message, embeddings_transcripts, st.session_state.bedrock_chat)
        st.session_state.retrieved_contexts = retrieved_contexts
        st.session_state.generated_response = response

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Retrieved Context")
        if 'retrieved_contexts' in st.session_state and st.session_state.retrieved_contexts:
            for context in st.session_state.retrieved_contexts:
                st.info(context)
        else:
            st.info("No additional context found.")
        
    with col2:
        st.subheader("Generated Response")
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

def render_interactive_stage():
    """Render the interactive learning stage"""
    st.header("Interactive Learning")
    
    if 'bedrock_chat' not in st.session_state:
        st.session_state.bedrock_chat = BedrockChat()
    
    col1, col2, col3 = st.columns(3)
   
    with col1:
        # Selectbox for Topic
        topics = ["Shopping", "Travel", "Food and Drink", "Health", "Education", "Work", "Hobbies", "Weather", "Family and Friends"]
        selected_topic = st.selectbox("Topic", topics)
    
    with col2:
        # Selectbox for Question Type
        question_types = ["Multiple Choice", "True/False"]
        selected_question_type = st.selectbox("Question Type", question_types)
    
    with col3:
        # Selectbox for Difficulty Level
        difficulty_levels = ["HSK 2", "Over HSK 2", "Under HSK 2"]
        selected_difficulty_level = st.selectbox("Difficulty Level", difficulty_levels)
    
    query = st.text_input(
        "Custom Input",
        placeholder="Optional customized input (if none, enter a blank space and press enter).",
        key="interactive_query_input"
    )
    
    if query:
        system_prompt = "You are an expert in HSK (Hanyu Shuiping Kaoshi) listening tests. You will be given the examples of HSK 2 listening test audio transcripts from sections 3 and 4 that best match the user's option selections and their own input. You must produce a new HSK test script and answer choices that fit the categories and options the user has selected and input. One of the answer choices must be noticeably better match than the others for the context of the script you produce. Do not give the answer to the user. You must only reply in simplified Chinese."
        
        # Concatenate system prompt, selected keywords, and user query
        combined_query = (
            system_prompt + "\n\n" +
            "Topic: " + selected_topic + "\n" +
            "Question Type: " + selected_question_type + "\n" +
            "Difficulty Level: " + selected_difficulty_level + "\n\n" +
            query
        )
        
        hsk2_data = read_hsk2_data('backend/data/HSK2_data.md')
        embeddings_transcripts = load_embeddings_with_hsk2_data('backend/data', hsk2_data)
        retrieved_contexts, response = process_rag_message(combined_query, embeddings_transcripts, st.session_state.bedrock_chat)
        st.session_state.retrieved_contexts = retrieved_contexts
        st.session_state.generated_response = response

        # Save the generated response to a text file with timestamp
        output_dir = 'backend/data/int_resp/'
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file_path = os.path.join(output_dir, f'int_resp_{timestamp}.txt')
        
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(st.session_state.generated_response)

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Retrieved Context")
        if 'retrieved_contexts' in st.session_state and st.session_state.retrieved_contexts:
            for context in st.session_state.retrieved_contexts:
                st.info(context)
        else:
            st.info("No additional context found.")
        
    with col2:
        st.subheader("Generated Response")
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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set the base directory to the absolute path of your project
BASE_DIR = '/absolute/path/to/your/project'

def process_text_files(input_dir, output_dir):
    """Your actual audio processing function"""
    logging.info(f"Processing files from {input_dir} to {output_dir}")
    # Your actual processing logic here
    # Example: Convert text files to audio files and save them in the output directory
    for filename in os.listdir(input_dir):
        if filename.endswith('.txt'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename.replace('.txt', '.mp3'))
            # Simulate processing
            with open(input_path, 'r') as infile, open(output_path, 'w') as outfile:
                content = infile.read()
                outfile.write(f"Processed audio content for: {content}")
            logging.info(f"Processed {input_path} to {output_path}")

def render_interactive_response_audio():
    """Render the interactive response audio stage"""
    st.header("Interactive Response Audio")
    
    # Set the absolute paths for the audio and input directories
    base_dir = os.path.dirname(os.path.abspath(__file__))
    audio_dir = os.path.join(base_dir, '../backend/data/audio/')
    input_dir = os.path.join(base_dir, '../backend/data/int_resp/')
    
    # Check if the audio directory exists, create if it doesn't
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)
        st.warning(f"Directory not found. Created new directory: {audio_dir}")
        logging.warning(f"Directory not found. Created new directory: {audio_dir}")
    
    # List all .mp3 files in the audio directory
    audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.mp3')]
    
    # List all .txt files in the input directory
    text_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
    
    # Find text files that do not have corresponding audio files
    missing_audio_files = [f for f in text_files if f.replace('int_resp_', 'audio_').replace('.txt', '.mp3') not in audio_files]
    
    st.subheader("Play Saved Audio")
    if audio_files:
        selected_audio_file = st.selectbox("Select an audio file to play", audio_files)
        if selected_audio_file:
            st.audio(os.path.join(audio_dir, selected_audio_file))
    else:
        st.info("No audio files available to play.")
    
    st.subheader("Create Audio for Saved Responses")
    if missing_audio_files:
        selected_text_file = st.selectbox("Select an interactice learning response to process", missing_audio_files)
        
        if selected_text_file:
            st.text_area("Text content", open(os.path.join(input_dir, selected_text_file)).read(), height=200)
        
        # Add a button to trigger the audio processing
        if st.button("Create Audio"):
            output_dir = audio_dir
            tts_script_path = os.path.join(base_dir, '../backend/tts.py')
            try:
                subprocess.run(['python', tts_script_path], check=True)
                st.success("Audio created successfully!")
            except subprocess.CalledProcessError as e:
                st.error(f"Audio creation failed: {e}")
    else:
        st.info("All saved responses corresponding audio files.")

def main():
    """Main function to render the selected stage"""
    render_header()  # Add this line to show the header
    selected_stage = render_sidebar()
    
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
    elif selected_stage == "6. Interactive Response Audio":
        render_interactive_response_audio()

if __name__ == "__main__":
    main()