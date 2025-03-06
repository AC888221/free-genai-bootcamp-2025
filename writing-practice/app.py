# app.py (added back)

import streamlit as st
from PIL import Image
import os
from frontend.styling import apply_styling
from frontend.state_management import change_state, generate_new_sentence
from backend.ocr_reader import load_ocr_reader
from backend.audio_generation import generate_audio
from backend.image_processing import process_and_grade_image
from backend.sentence_generation import SentenceGenerator
from word_collection import fetch_word_collection  # Import the combined module
import config
import logging
import random

# Define a custom hash function for Logger
def hash_logger(obj):
    return (obj.name, obj.level)

# Set page config
st.set_page_config(
    page_title="Putonghua Learning App",
    page_icon="🀄",
    layout="wide"  # Change layout to 'wide'
)

# Use API URL from config
API_URL = config.API_URL

# Initialize session state if needed
if 'setup_state' not in st.session_state:
    st.session_state['setup_state'] = 'word_collection'  # Set initial state to 'word_collection'
if 'current_state' not in st.session_state:
    st.session_state['current_state'] = 'setup'  # Set initial state to 'setup'
if 'current_sentence' not in st.session_state:
    st.session_state['current_sentence'] = {}
if 'grading_results' not in st.session_state:
    st.session_state['grading_results'] = {}
if 'uploaded_image' not in st.session_state:
    st.session_state['uploaded_image'] = None

# Load OCR reader
reader = load_ocr_reader()

# Apply styling
apply_styling()

# Function to generate a new sentence using SentenceGenerator
def generate_sentence_for_app(api_url, group_id, _word=None):
    try:
        sentence_generator = SentenceGenerator()
        result = sentence_generator.generate_sentence(_word if _word else "学习")
        
        if "error" in result:
            st.error(f"Error generating sentence: {result['error']}")
        else:
            # Ensure the result contains the necessary keys
            if all(key in result for key in ["english", "chinese", "pinyin"]):
                st.session_state['current_sentence'] = result
                # Optionally store the sentence if needed
                if api_url and group_id:
                    try:
                        sentence_generator.store_sentence(api_url, group_id, result)
                    except Exception as e:
                        st.warning(f"Could not store sentence: {e}")
            else:
                st.error("Error: Generated sentence does not contain all required keys.")
        return result
    except Exception as e:
        st.error(f"Error in generate_sentence_for_app: {e}")
        return {"error": str(e)}

# Sidebar for navigation
with st.sidebar:
    st.header("Welcome")
    st.markdown(config.WELCOME_TEXT)
    
    st.header("Navigation")
    if st.button("Word Collection"):
        st.session_state['setup_state'] = 'word_collection'
        st.session_state['current_state'] = 'setup'
    if st.button("Writing Practice"):
        st.session_state['current_state'] = 'practice'
    if st.button("Review and Grading"):
        st.session_state['current_state'] = 'review'
    
    st.header("About")
    st.markdown(config.ABOUT_TEXT)

# Main app logic based on current state
if st.session_state['current_state'] == 'setup':
    if st.session_state['setup_state'] == 'word_collection':
        # Word Collection State
        st.markdown('<h1 class="main-header">Word Collection</h1>', unsafe_allow_html=True)
        
        # Fetch words from the desired source (either 'db' or 'api')
        source = 'api'  # Change to 'db' if you want to fetch from the database
        db_path = 'backend-flask/words.db'
        print(f"Fetching words from source: {source}, API URL: {API_URL}")
        st.session_state['word_collection'] = fetch_word_collection(source, db_path=db_path, api_url=API_URL)
        
        # Filter out unnecessary columns and remove duplicates based on 'jiantizi'
        unique_words = set()
        filtered_word_collection = []
        for word in st.session_state['word_collection']:
            filtered_word = {key: value for key, value in word.items() if key not in ['ID', 'correct_count', 'wrong_count']}
            chinese_word = filtered_word.get('jiantizi')  # Assuming 'jiantizi' is the key for the Chinese word
            if chinese_word not in unique_words:
                unique_words.add(chinese_word)
                filtered_word_collection.append(filtered_word)
        
        # Display filtered word collection in a styled table
        st.markdown('''
            <style>
            .word-table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 2rem;
            }
            .word-table th, .word-table td {
                border: 1px solid #DDDDDD;
                padding: 0.5rem;
                text-align: left;
            }
            .word-table th {
                font-size: 1.875rem;  /* Increased by 25% */
                color: #4B0082;
                background-color: #F0F8FF;
            }
            .word-table td {
                font-size: 1.5rem;  /* Increased by 25% */
                color: #333333;
            }
            </style>
        ''', unsafe_allow_html=True)

        st.markdown('<table class="word-table"><thead><tr><th>English</th><th>Chinese</th><th>Pinyin</th></tr></thead><tbody>', unsafe_allow_html=True)
        for word in filtered_word_collection:
            st.markdown(f'<tr><td>{word["english"]}</td><td class="chinese-text">{word["jiantizi"]}</td><td>{word["pinyin"]}</td></tr>', unsafe_allow_html=True)
        st.markdown('</tbody></table>', unsafe_allow_html=True)

elif st.session_state['current_state'] == 'practice':
    # Writing Practice Stage
    st.markdown('<h1 class="main-header">Putonghua Learning App</h1>', unsafe_allow_html=True)
    
    # Word Selection - Ensure unique Chinese characters
    st.markdown('<h2 class="sub-header">Select a Word:</h2>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([3, 1, 3])
    
    with col1:
        # Create a list of unique Chinese characters
        unique_chinese_words = []
        seen_words = set()
        for word in st.session_state['word_collection']:
            chinese_word = word['jiantizi']
            if chinese_word not in seen_words:
                seen_words.add(chinese_word)
                unique_chinese_words.append(chinese_word)
        
        selected_word = st.selectbox("Choose a word from your collection:", unique_chinese_words)
    
    with col2:
        st.markdown("""
            <style>
            .random-button {
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100%;
                background-color: #FF6347;  /* Brighter color */
                color: white;
                font-size: 1.2rem;
                padding: 0.5rem;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            .random-button:hover {
                background-color: #FF4500;  /* Darker shade on hover */
            }
            </style>
            <button class="random-button" onclick="window.location.href=window.location.href">Choose Random Word</button>
        """, unsafe_allow_html=True)
    
    with col3:
        input_word = st.text_input("Or input a new word:")
        if input_word:
            selected_word = input_word
    
    if selected_word:
        generate_sentence_for_app(API_URL, group_id=1, _word=selected_word)
    
    # Display Sentence for Translation
    if 'current_sentence' in st.session_state and st.session_state['current_sentence']:
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
        
        # Instructions for writing practice
        st.markdown('<div class="instruction-text">Write the Chinese characters on paper, then proceed to the Review stage to upload your writing.</div>', unsafe_allow_html=True)
        
        # Button to proceed to review stage
        if st.button("Proceed to Review"):
            st.session_state['current_state'] = 'review'
            st.experimental_rerun()

elif st.session_state['current_state'] == 'review':
    # Grading and Review Stage
    st.markdown('<h1 class="main-header">Putonghua Learning App</h1>', unsafe_allow_html=True)
    
    # Original English sentence
    if "english" in st.session_state["current_sentence"]:
        st.markdown(f'<div class="instruction-text">{st.session_state["current_sentence"]["english"]}</div>', unsafe_allow_html=True)
    else:
        st.error("Error: 'english' key not found in the current sentence.")
    
    # Expected Chinese sentence
    if "chinese" in st.session_state["current_sentence"]:
        st.markdown(f'<h2 class="sub-header">Expected Chinese:</h2>', unsafe_allow_html=True)
        st.markdown(f'<div class="chinese-text">{st.session_state["current_sentence"]["chinese"]}</div>', unsafe_allow_html=True)
    else:
        st.error("Error: 'chinese' key not found in the current sentence.")
    
    # Pinyin
    if "pinyin" in st.session_state["current_sentence"]:
        st.markdown(f'<div class="pinyin-text">{st.session_state["current_sentence"]["pinyin"]}</div>', unsafe_allow_html=True)
    else:
        st.error("Error: 'pinyin' key not found in the current sentence.")
    
    # Audio playback
    if "chinese" in st.session_state["current_sentence"]:
        audio_bytes = generate_audio(st.session_state["current_sentence"]["chinese"])
        st.audio(audio_bytes, format="audio/mp3")
    
    # Image upload section with clear instructions
    st.markdown('<h2 class="sub-header">Upload Your Writing</h2>', unsafe_allow_html=True)
    st.markdown('<div class="instruction-text">Take a photo of your handwritten Chinese characters and upload it here:</div>', unsafe_allow_html=True)
    
    # Use a unique key for the file uploader to ensure it refreshes properly
    uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"], key="writing_image_uploader")
    
    # Only show grading if an image has been uploaded
    if uploaded_file is not None:
        try:
            # Display a success message
            st.success("Image uploaded successfully!")
            
            # Open and display the image
            image = Image.open(uploaded_file)
            st.session_state['uploaded_image'] = image
            st.image(image, caption="Your uploaded writing", use_column_width=True)
            
            # Process and grade the image
            grade_button = st.button("Grade My Writing", key="grade_writing_button")
            if grade_button:
                with st.spinner("Analyzing your writing..."):
                    results = process_and_grade_image(image, st.session_state["current_sentence"]["chinese"])
                    st.session_state['grading_results'] = results
                    st.experimental_rerun()
        except Exception as e:
            st.error(f"Error processing the uploaded image: {str(e)}")
            st.session_state['uploaded_image'] = None
    else:
        # Show a placeholder or instructions when no image is uploaded
        st.info("Please upload an image of your handwritten Chinese characters to proceed with grading.")
    
    # Display grading results if available
    if 'grading_results' in st.session_state and st.session_state['grading_results']:
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

    # Sidebar navigation for next actions
    with st.sidebar:
        st.header("Next Actions")
        if st.button("Try Again", key="try_again_button"):
            st.session_state['current_state'] = 'practice'
            st.session_state['grading_results'] = {}
            st.session_state['uploaded_image'] = None
            st.experimental_rerun()

        if st.button("New Sentence", key="new_sentence_button"):
            generate_sentence_for_app(API_URL, group_id=1)  # Provide a valid group_id
            st.session_state['uploaded_image'] = None
            st.experimental_rerun()

elif st.session_state['current_state'] == 'collection':
    # Word Collection Stage
    st.markdown('<h1 class="main-header">Putonghua Learning App</h1>', unsafe_allow_html=True)
    st.markdown('<h2 class="sub-header">Your Word Collection</h2>', unsafe_allow_html=True)
    
    # Add custom CSS for better table styling
    st.markdown("""
    <style>
    .word-collection-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 20px;
    }
    .word-collection-table th {
        background-color: #f0f0f0;
        padding: 10px;
        text-align: center;
        font-weight: bold;
        border: 1px solid #ddd;
    }
    .word-collection-table td {
        padding: 10px;
        text-align: center;
        border: 1px solid #ddd;
    }
    .word-collection-table tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    .word-collection-table tr:hover {
        background-color: #f1f1f1;
    }
    .chinese-cell {
        font-size: 24px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create a proper HTML table for word collection
    if 'word_collection' in st.session_state and st.session_state['word_collection']:
        table_html = """
        <table class="word-collection-table">
            <thead>
                <tr>
                    <th>Chinese</th>
                    <th>Pinyin</th>
                    <th>English</th>
                    <th>Traditional</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for word in st.session_state['word_collection']:
            table_html += f"""
            <tr>
                <td class="chinese-cell">{word.get('jiantizi', '')}</td>
                <td>{word.get('pinyin', '')}</td>
                <td>{word.get('english', '')}</td>
                <td class="chinese-cell">{word.get('fantizi', '')}</td>
            </tr>
            """
        
        table_html += """
            </tbody>
        </table>
        """
        
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.info("Your word collection is empty. Add words during practice to see them here.")
    
    # Add a word manually
    st.markdown('<h3 class="sub-header">Add a Word Manually</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_word = st.text_input("Chinese Character (Simplified):")
    
    with col2:
        if new_word:
            if st.button("Add to Collection"):
                add_word_to_collection(new_word)
                st.success(f"Added '{new_word}' to your collection!")
                st.experimental_rerun()
    
    # Navigation
    if st.button("Back to Practice"):
        st.session_state['current_state'] = 'practice'
        st.experimental_rerun()