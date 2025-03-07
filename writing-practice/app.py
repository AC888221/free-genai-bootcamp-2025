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
import pandas as pd

# Set page config - MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Putonghua Learning App",
    page_icon="🀄",
    layout="wide"  # Change layout to 'wide'
)

# Define a custom hash function for Logger
def hash_logger(obj):
    return (obj.name, obj.level)

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
        word_collection = fetch_word_collection(source, db_path=db_path, api_url=API_URL)
        
        # Filter out unnecessary columns and remove duplicates based on 'jiantizi'
        unique_words = set()
        filtered_word_collection = []
        
        for word in word_collection:
            # Extract the relevant fields
            if isinstance(word, dict):
                chinese_word = word.get('jiantizi', '')
                english = word.get('english', '')
                pinyin = word.get('pinyin', '')
            else:
                # Handle case where word might be a tuple from DB
                chinese_word = word[1] if len(word) > 1 else ''
                english = word[3] if len(word) > 3 else ''
                pinyin = word[2] if len(word) > 2 else ''
            
            if chinese_word and chinese_word not in unique_words:
                unique_words.add(chinese_word)
                filtered_word_collection.append({
                    'English': english,
                    'Chinese': chinese_word,
                    'Pinyin': pinyin
                })
        
        # Convert to DataFrame for better display
        df = pd.DataFrame(filtered_word_collection)
        
        # Apply custom CSS for better display
        st.markdown("""
        <style>
        .dataframe {
            font-size: 18px !important;
            width: 100% !important;
        }
        .dataframe th {
            text-align: left !important;
            background-color: #f2f2f2 !important;
            color: #333 !important;
            font-weight: bold !important;
            padding: 12px !important;
        }
        .dataframe td {
            text-align: left !important;
            padding: 12px !important;
        }
        /* Make Chinese characters larger */
        .dataframe td:nth-child(2) {
            font-size: 24px !important;
        }
        /* Hide the index column */
        .dataframe th:first-child,
        .dataframe td:first-child {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Display the DataFrame without the index column
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Store in session state for later use
        st.session_state['word_collection'] = word_collection

elif st.session_state['current_state'] == 'practice':
    # Writing Practice Stage
    st.markdown('<h1 class="main-header">Putonghua Learning App</h1>', unsafe_allow_html=True)
    
    # Word Selection - Ensure unique Chinese characters
    st.markdown('<h2 class="sub-header">Select a Word:</h2>', unsafe_allow_html=True)
    
    # Create a list of unique Chinese characters
    unique_chinese_words = []
    seen_words = set()
    for word in st.session_state['word_collection']:
        if isinstance(word, dict):
            chinese_word = word.get('jiantizi', '')
        else:
            # Handle case where word might be a tuple from DB
            chinese_word = word[1] if len(word) > 1 else ''
            
        if chinese_word and chinese_word not in seen_words:
            seen_words.add(chinese_word)
            unique_chinese_words.append(chinese_word)
    
    # Initialize selected_word in session state if not present
    if 'selected_word' not in st.session_state:
        st.session_state['selected_word'] = ""
    
    # Create a 3-column layout for word selection
    col1, col2, col3 = st.columns([3, 1, 3])
    
    with col1:
        selected_word_from_list = st.selectbox("Choose a word from your collection:", 
                                              [""] + unique_chinese_words,
                                              index=0)
        if selected_word_from_list:
            st.session_state['selected_word'] = selected_word_from_list
    
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
        """, unsafe_allow_html=True)
        
        if st.button("Choose Random Word"):
            if unique_chinese_words:
                st.session_state['selected_word'] = random.choice(unique_chinese_words)
    
    with col3:
        input_word = st.text_input("Or input a new word:")
        if st.button("Use this word") and input_word:
            st.session_state['selected_word'] = input_word
    
    # Display the selected word and generate sentence button
    st.markdown("""
        <style>
        .word-display {
            margin-top: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
            border-left: 5px solid #4CAF50;
        }
        .selected-word {
            font-size: 28px;
            font-weight: bold;
            color: #333;
        }
        .generate-container {
            display: flex;
            align-items: center;
            margin-top: 20px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Display the selected word and generate button in a single row
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.session_state['selected_word']:
            st.markdown(f"""
                <div class="word-display">
                    <div>Selected Word:</div>
                    <div class="selected-word">{st.session_state['selected_word']}</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="word-display">
                    <div>Selected Word:</div>
                    <div class="selected-word">No word selected</div>
                </div>
            """, unsafe_allow_html=True)
    
    with col2:
        generate_button_disabled = not st.session_state['selected_word']
        if st.button("Generate Sentence", disabled=generate_button_disabled):
            generate_sentence_for_app(API_URL, group_id=1, _word=st.session_state['selected_word'])
    
    # Display Sentence for Translation
    if 'current_sentence' in st.session_state and st.session_state['current_sentence'] and 'chinese' in st.session_state['current_sentence']:
        st.markdown(f'<h2 class="sub-header">Translate this sentence:</h2>', unsafe_allow_html=True)
        st.markdown(f'<div class="instruction-text">{st.session_state["current_sentence"]["english"]}</div>', unsafe_allow_html=True)
        
        # Show Pinyin toggle
        show_pinyin = st.checkbox("Show Pinyin")
        if show_pinyin:
            st.markdown(f'<div class="pinyin-text">{st.session_state["current_sentence"]["pinyin"]}</div>', unsafe_allow_html=True)
        
        # Audio playback
        audio_bytes = generate_audio(st.session_state["current_sentence"]["chinese"])
        st.audio(audio_bytes, format="audio/mp3")
        
        # Instructions for writing practice
        st.markdown("""
            <div class="instruction-text">
                1. Listen to the audio for pronunciation
                2. Write the Chinese characters on paper
                3. Proceed to the Review stage to check your writing
            </div>
        """, unsafe_allow_html=True)
        
        # Button to proceed to review stage
        if st.button("Proceed to Review"):
            st.session_state['current_state'] = 'review'
            st.rerun()

elif st.session_state['current_state'] == 'review':
    # Grading and Review Stage
    st.markdown('<h1 class="main-header">Putonghua Learning App</h1>', unsafe_allow_html=True)
    
    # Check if a sentence has been generated
    if not st.session_state["current_sentence"] or "chinese" not in st.session_state["current_sentence"]:
        # Display a friendly message prompting the user to generate a sentence first
        st.info("Please go to the Writing Practice section and generate a sentence first before reviewing.")
        
        # Add a button to navigate to practice section
        if st.button("Go to Writing Practice"):
            st.session_state['current_state'] = 'practice'
            st.experimental_rerun()
    else:
        # Original English sentence
        st.markdown(f'<div class="instruction-text">{st.session_state["current_sentence"]["english"]}</div>', unsafe_allow_html=True)
        
        # Expected Chinese sentence
        st.markdown(f'<h2 class="sub-header">Expected Chinese:</h2>', unsafe_allow_html=True)
        st.markdown(f'<div class="chinese-text">{st.session_state["current_sentence"]["chinese"]}</div>', unsafe_allow_html=True)
        
        # Pinyin
        st.markdown(f'<div class="pinyin-text">{st.session_state["current_sentence"]["pinyin"]}</div>', unsafe_allow_html=True)
        
        # Audio playback
        audio_bytes = generate_audio(st.session_state["current_sentence"]["chinese"])
        st.audio(audio_bytes, format="audio/mp3")
        
        # Image upload section with clear instructions
        st.markdown('<h2 class="sub-header">Upload Your Writing</h2>', unsafe_allow_html=True)
        st.markdown('<div class="instruction-text">Try one of these methods to upload your handwritten Chinese characters:</div>', unsafe_allow_html=True)
        
        # Create a radio button to select the upload method
        upload_method = st.radio(
            "Select upload method:",
            ["Standard File Uploader", "Camera Input", "Alternative Uploader", "URL Input"],
            key="upload_method"
        )
        
        # Method 1: Standard File Uploader
        if upload_method == "Standard File Uploader":
            st.subheader("Standard File Uploader")
            uploaded_file1 = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"], key="uploader1")
            if uploaded_file1 is not None:
                st.session_state['uploaded_image'] = Image.open(uploaded_file1)
                st.image(st.session_state['uploaded_image'], caption="Uploaded with Standard Uploader", use_column_width=True)
        
        # Method 2: Camera Input
        elif upload_method == "Camera Input":
            st.subheader("Camera Input")
            try:
                camera_input = st.camera_input("Take a picture", key="camera_input")
                if camera_input is not None:
                    st.session_state['uploaded_image'] = Image.open(camera_input)
                    st.image(st.session_state['uploaded_image'], caption="Captured with camera", use_column_width=True)
            except Exception as e:
                st.error(f"Camera input not available: {str(e)}")
                st.info("Your version of Streamlit might not support camera input. Try upgrading Streamlit or use another method.")
        
        # Method 3: Alternative Uploader
        elif upload_method == "Alternative Uploader":
            st.subheader("Alternative File Uploader")
            col1, col2 = st.columns(2)
            with col1:
                uploaded_file3 = st.file_uploader("Choose file", type=["jpg", "jpeg", "png"], key="uploader3")
            with col2:
                if st.button("Confirm Upload", key="confirm_upload"):
                    if 'uploaded_file3' in locals() and uploaded_file3 is not None:
                        st.session_state['uploaded_image'] = Image.open(uploaded_file3)
                        st.image(st.session_state['uploaded_image'], caption="Uploaded with Alternative Uploader", use_column_width=True)
                    else:
                        st.error("Please select a file first")
        
        # Method 4: URL Input
        elif upload_method == "URL Input":
            st.subheader("URL Input")
            image_url = st.text_input("Enter image URL:", key="image_url")
            if st.button("Load from URL", key="load_url"):
                if image_url:
                    try:
                        import requests
                        from io import BytesIO
                        response = requests.get(image_url)
                        st.session_state['uploaded_image'] = Image.open(BytesIO(response.content))
                        st.image(st.session_state['uploaded_image'], caption="Loaded from URL", use_column_width=True)
                    except Exception as e:
                        st.error(f"Error loading image from URL: {str(e)}")
                else:
                    st.error("Please enter a valid URL")
        
        # Display the currently uploaded image (if any)
        if 'uploaded_image' in st.session_state and st.session_state['uploaded_image'] is not None:
            st.markdown('<h3 class="sub-header">Your Uploaded Image:</h3>', unsafe_allow_html=True)
            st.image(st.session_state['uploaded_image'], caption="Your writing", use_column_width=True)
            
            # Add a grade button
            if st.button("Grade My Writing", key="grade_writing_button"):
                with st.spinner("Analyzing your writing..."):
                    results = process_and_grade_image(st.session_state['uploaded_image'], 
                                                     st.session_state["current_sentence"]["chinese"])
                    st.session_state['grading_results'] = results
                    st.experimental_rerun()
        
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
        table-layout: fixed;
    }
    .word-collection-table th {
        background-color: #f0f0f0;
        padding: 12px 15px;
        text-align: center;
        font-weight: bold;
        border: 1px solid #ddd;
        font-size: 18px;
    }
    .word-collection-table td {
        padding: 12px 15px;
        text-align: center;
        border: 1px solid #ddd;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    .word-collection-table tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    .word-collection-table tr:hover {
        background-color: #f1f1f1;
    }
    .chinese-cell {
        font-size: 24px;
        font-weight: normal;
    }
    .word-collection-table th:nth-child(1),
    .word-collection-table td:nth-child(1) {
        width: 20%;
    }
    .word-collection-table th:nth-child(2),
    .word-collection-table td:nth-child(2) {
        width: 25%;
    }
    .word-collection-table th:nth-child(3),
    .word-collection-table td:nth-child(3) {
        width: 35%;
    }
    .word-collection-table th:nth-child(4),
    .word-collection-table td:nth-child(4) {
        width: 20%;
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