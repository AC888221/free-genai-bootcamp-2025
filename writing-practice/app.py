# app.py (addded back)

import streamlit as st
from PIL import Image
import os
from frontend.styling import apply_styling
from frontend.state_management import change_state, generate_new_sentence
from backend.ocr_reader import load_ocr_reader
from backend.audio_generation import generate_audio
from backend.image_processing import process_and_grade_image
from backend.sentence_generation import generate_sentence
from word_collection import fetch_word_collection  # Import the combined module
import config

# Set page config
st.set_page_config(
    page_title="Putonghua Learning App",
    page_icon="🀄",
    layout="centered"
)

# Use API URL and group ID from config
API_URL = config.API_URL
GROUP_ID = config.GROUP_ID

# Initialize session state if needed
if 'current_state' not in st.session_state:
    st.session_state['current_state'] = 'setup'
if 'word_collection' not in st.session_state:
    st.session_state['word_collection'] = []
if 'current_sentence' not in st.session_state:
    st.session_state['current_sentence'] = {}
if 'grading_results' not in st.session_state:
    st.session_state['grading_results'] = {}

# Load OCR reader
reader = load_ocr_reader()

# Apply styling
apply_styling()

# Fetch words from the desired source (either 'db' or 'api')
source = 'api'  # Change to 'db' if you want to fetch from the database
db_path = 'backend-flask/words.db'
st.session_state['word_collection'] = fetch_word_collection(source, db_path=db_path, api_url=API_URL, group_id=GROUP_ID)

# Function to generate a new sentence
def generate_new_sentence(api_url, group_id):
    st.session_state['current_sentence'] = generate_sentence(api_url, group_id, _word=None)

# Main app logic based on current state
if st.session_state['current_state'] == 'setup':
    # Setup State
    st.markdown('<h1 class="main-header">Putonghua Learning App</h1>', unsafe_allow_html=True)
    st.markdown(config.WELCOME_TEXT)
    
    # Display fetched words
    st.markdown("### Word Collection")
    st.write(st.session_state['word_collection'])
    
    if st.button("Start Learning"):
        generate_new_sentence(API_URL, GROUP_ID)
        st.experimental_rerun()

elif st.session_state['current_state'] == 'practice':
    # Practice State
    st.markdown('<h1 class="main-header">Putonghua Learning App</h1>', unsafe_allow_html=True)
    
    # Display English sentence
    st.markdown(f'<h2 class="sub-header">Translate this sentence:</h2>', unsafe_allow_html=True)
    st.markdown(f'<div class="instruction-text">{st.session_state["current_sentence"]["english"]}</div>', unsafe_allow_html=True)
    
    # Show Pinyin toggle
    show_pinyin = st.checkbox("Show Pinyin")
    if show_pinyin:
        st.markdown(f'<div class="pinyin-text">{st.session_state["current_sentence"]["pinyin"]}</div>', unsafe_allow_html=True)
    
    # Show expected Chinese (hidden in real app, shown here for testing)
    if st.checkbox("Show Expected Chinese (for testing only)"):
        st.markdown(f'<div class="chinese-text">{st.session_state["current_sentence"]["chinese"]}</div>', unsafe_allow_html=True)
    
    # Audio playback
    audio_bytes = generate_audio(st.session_state["current_sentence"]["chinese"])
    st.audio(audio_bytes, format="audio/mp3")
    
    # Image upload
    st.markdown('<div class="instruction-text">Write the Chinese characters and upload an image of your writing:</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload your handwritten Chinese", type=["jpg", "jpeg", "png"])
    
    # Preview uploaded image
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Your uploaded writing", use_column_width=True)
        
        # Submit button
        if st.button("Submit for Review"):
            # Show a spinner while processing
            with st.spinner("Analyzing your writing with Claude 3 Haiku..."):
                results = process_and_grade_image(image, st.session_state["current_sentence"]["chinese"])
                st.session_state['grading_results'] = results
                st.session_state['current_state'] = 'review'
                st.experimental_rerun()

elif st.session_state['current_state'] == 'review':
    # Review State
    st.markdown('<h1 class="main-header">Putonghua Learning App</h1>', unsafe_allow_html=True)
    
    # Original English sentence
    st.markdown(f'<h2 class="sub-header">Original Sentence:</h2>', unsafe_allow_html=True)
    st.markdown(f'<div class="instruction-text">{st.session_state["current_sentence"]["english"]}</div>', unsafe_allow_html=True)
    
    # Expected Chinese sentence
    st.markdown(f'<h2 class="sub-header">Expected Chinese:</h2>', unsafe_allow_html=True)
    st.markdown(f'<div class="chinese-text">{st.session_state["current_sentence"]["chinese"]}</div>', unsafe_allow_html=True)
    
    # Pinyin
    st.markdown(f'<div class="pinyin-text">{st.session_state["current_sentence"]["pinyin"]}</div>', unsafe_allow_html=True)
    
    # Audio playback
    audio_bytes = generate_audio(st.session_state["current_sentence"]["chinese"])
    st.audio(audio_bytes, format="audio/mp3")
    
    # Show user's submission
    st.markdown(f'<h2 class="sub-header">Your Writing:</h2>', unsafe_allow_html=True)
    
    # Review results
    results = st.session_state['grading_results']
    
    # Display transcription
    st.markdown("**Transcription of your writing:**")
    st.markdown(f'<div class="chinese-text">{results["transcription"]}</div>', unsafe_allow_html=True)
    
    # Display back translation
    st.markdown("**Translation of your writing:**")
    st.markdown(f'<div class="instruction-text">{results["back_translation"]}</div>', unsafe_allow_html=True)
    
    # Display grade with appropriate color
    grade_class = f"grade-{results['grade'].lower()}"
    st.markdown(f'<h2 class="sub-header">Grade: <span class="{grade_class}">{results["grade"]}</span></h2>', unsafe_allow_html=True)
    
    # Progress bar for accuracy
    st.progress(results["accuracy"])
    
    # Feedback
    st.markdown("**Feedback:**")
    st.markdown(f'<div class="instruction-text">{results["feedback"]}</div>', unsafe_allow_html=True)
    
    # Character comparison
    st.markdown("**Character Comparison:**")
    
    # Create columns for side-by-side comparison
    cols = st.columns(len(results["char_comparison"]))
    
    for i, char_data in enumerate(results["char_comparison"]):
        with cols[i]:
            # Expected character
            st.markdown("Expected:")
            if char_data["expected"]:
                st.markdown(f'<div class="chinese-text">{char_data["expected"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown("—")
            
            # User's character with color coding
            st.markdown("Your writing:")
            if char_data["written"]:
                css_class = "char-correct" if char_data["correct"] else "char-incorrect"
                st.markdown(f'<div class="chinese-text {css_class}">{char_data["written"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown("—")

# Buttons for next actions
col1, col2 = st.columns(2)
with col1:
    if st.button("Try Again"):
        st.session_state['current_state'] = 'practice'
        st.session_state['grading_results'] = {}
        st.experimental_rerun()

with col2:
    if st.button("New Sentence"):
        generate_new_sentence(API_URL, GROUP_ID)
        st.experimental_rerun()