# app.py (main entry point)

import streamlit as st
from PIL import Image
import os
import sys
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
from difflib import SequenceMatcher
import io
import traceback
from datetime import datetime
from typing import Optional
import boto3
from botocore.exceptions import ProfileNotFound
import requests  # Add this import for making API calls

# Configure logging
log_file = f"writelab_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class Config:
    """Application configuration."""
    def __init__(self):
        # Get credentials from AWS CLI configuration
        try:
            session = boto3.Session()
            credentials = session.get_credentials()
            if credentials:
                self.AWS_ACCESS_KEY_ID = credentials.access_key
                self.AWS_SECRET_ACCESS_KEY = credentials.secret_key
                self.AWS_DEFAULT_REGION = session.region_name or 'us-west-2'
                logger.info("AWS credentials loaded from AWS CLI configuration")
            else:
                raise ValueError("No AWS credentials found in AWS CLI configuration")
                
        except (ProfileNotFound, ValueError) as e:
            logger.error(f"AWS CLI credentials not found: {str(e)}")
            logger.error("Please run 'aws configure' to set up your AWS credentials")
            raise
        
        # Import from config.py
        self.LANG_PORTAL_URL = config.LANG_PORTAL_URL  # For fetching words from lang-portal
        self.WELCOME_TEXT = config.WELCOME_TEXT
        self.ABOUT_TEXT = config.ABOUT_TEXT

def setup_streamlit():
    """Initialize Streamlit configuration and session state."""
    logger.info("Setting up Streamlit configuration")
    try:
        # Set page config - MUST BE THE FIRST STREAMLIT COMMAND
        st.set_page_config(
            page_title="Putonghua Learning App",
            page_icon="🀄",
            layout="wide"  # Change layout to 'wide'
        )
        logger.debug("Page config set successfully")

        # Initialize session state BEFORE accessing it
        state_vars = {
            'setup_state': 'word_collection',
            'current_state': 'setup',
            'current_sentence': {},
            'grading_results': {},
            'uploaded_image': None
        }

        for var, default in state_vars.items():
            if var not in st.session_state:
                st.session_state[var] = default
                logger.debug(f"Initialized session state: {var}")

        return True

    except Exception as e:
        logger.error(f"Error in setup_streamlit: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def initialize_components():
    """Initialize app components."""
    logger.info("Initializing app components")
    try:
        # Load OCR reader
        reader = load_ocr_reader()
        logger.debug("OCR reader initialized")

        # Apply styling
        apply_styling()
        logger.debug("Styling applied")

        return reader
    except Exception as e:
        logger.error(f"Error in initialize_components: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def check_environment():
    """Check if AWS CLI is configured properly and lang-portal is accessible."""
    logger.info("Checking AWS configuration and lang-portal access")
    
    try:
        # Check AWS credentials
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if not (credentials and credentials.access_key and credentials.secret_key and session.region_name):
            logger.error("AWS credentials not found in AWS CLI configuration")
            st.error("""
                AWS credentials not found. Please configure AWS CLI:
                1. Install AWS CLI
                2. Run 'aws configure'
                3. Enter your AWS credentials and region
            """)
            return False
        
        # Check lang-portal connection (if needed)
        # Note: You might want to add a health check here
        
        logger.info("Environment check passed")
        return True
        
    except Exception as e:
        logger.error(f"Error checking configuration: {str(e)}")
        st.error("""
            Error checking configuration. Please make sure:
            1. AWS CLI is installed and configured
            2. Lang-portal server is running
        """)
        return False

def fetch_words_from_api(page=1, sort_by='jiantizi', order='asc'):
    """Fetch words from the API."""
    try:
        logger.info(f"Fetching words from API with params: page={page}, sort_by={sort_by}, order={order}")
        url = f"{config.LANG_PORTAL_URL}/words"
        logger.info(f"API URL: {url}")
        
        response = requests.get(url, params={
            'page': page,
            'sort_by': sort_by,
            'order': order
        })
        
        logger.info(f"API response status code: {response.status_code}")
        response.raise_for_status()  # Raise an error for bad responses
        
        data = response.json()
        logger.info(f"API response data type: {type(data)}")
        if isinstance(data, dict):
            logger.info(f"API response keys: {data.keys()}")
            if 'words' in data:
                logger.info(f"Found {len(data['words'])} words in API response")
            else:
                logger.warning("No 'words' key found in API response")
        
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching words from API: {str(e)}")
        return {'words': []}
    except ValueError as e:
        logger.error(f"JSON parsing error fetching words from API: {str(e)}")
        return {'words': []}
    except Exception as e:
        logger.error(f"Unexpected error fetching words from API: {str(e)}")
        logger.error(traceback.format_exc())
        return {'words': []}

def display_sidebar(config_obj):
    """Display the sidebar navigation."""
    with st.sidebar:
        st.header("Welcome")
        st.markdown(config_obj.WELCOME_TEXT)
        
        st.header("Navigation")
        if st.button("Word Collection"):
            st.session_state['setup_state'] = 'word_collection'
            st.session_state['current_state'] = 'setup'
        if st.button("Writing Practice"):
            st.session_state['current_state'] = 'practice'
        if st.button("Review and Grading"):
            st.session_state['current_state'] = 'review'
        
        st.header("About")
        st.markdown(config_obj.ABOUT_TEXT)

def display_word_collection(config_obj):
    """Display the word collection page."""
    st.markdown('<h1 class="main-header">Word Collection</h1>', unsafe_allow_html=True)
    
    # Fetch words from the API
    logger.info(f"Fetching words from API: {config_obj.LANG_PORTAL_URL}/words")
    api_response = fetch_words_from_api()
    word_collection = api_response.get('words', [])
    
    # Filter out unnecessary columns and remove duplicates based on 'jiantizi'
    unique_words = set()
    filtered_word_collection = []
    
    for word in word_collection:
        chinese_word = word.get('jiantizi', '')
        english = word.get('english', '')
        pinyin = word.get('pinyin', '')
        
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

def display_writing_practice(config_obj, reader):
    """Display the writing practice page."""
    try:
        # Writing Practice Stage
        st.markdown('<h1 class="main-header">Putonghua Learning App</h1>', unsafe_allow_html=True)
        logger.info("Entering writing practice stage")
        
        # Word Selection - Ensure unique Chinese characters
        st.markdown('<h2 class="sub-header">Select a Word:</h2>', unsafe_allow_html=True)
        
        # Create a list of unique Chinese characters
        unique_chinese_words = []
        seen_words = set()
        
        # Fetch fresh words from API
        logger.info("Fetching fresh words from API for practice stage")
        try:
            api_response = fetch_words_from_api()
            word_collection = api_response.get('words', [])
            logger.info(f"Fetched {len(word_collection)} words from API")
            
            st.session_state['word_collection'] = word_collection
            
            for word in word_collection:
                chinese_word = word.get('jiantizi', '')
                if chinese_word and chinese_word not in seen_words:
                    seen_words.add(chinese_word)
                    unique_chinese_words.append(chinese_word)
        except Exception as e:
            logger.error(f"Error fetching words from API: {str(e)}")
            logger.error(traceback.format_exc())
            st.error(f"Error fetching words: {str(e)}")
        
        logger.info(f"Found {len(unique_chinese_words)} unique Chinese words")
        
        # Initialize selected_word in session state if not present
        if 'selected_word' not in st.session_state:
            st.session_state['selected_word'] = ""
        
        # Create a 3-column layout for word selection
        col1, col2, col3 = st.columns([3, 1, 3])
        
        with col1:
            if unique_chinese_words:
                selected_word_from_list = st.selectbox("Choose a word from your collection:", 
                                                     [""] + unique_chinese_words,
                                                     index=0)
                if selected_word_from_list:
                    st.session_state['selected_word'] = selected_word_from_list
            else:
                st.error("No words available. Please check the API connection.")
        
        with col2:
            st.markdown("""
                <style>
                .random-button {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 100%;
                    background-color: #FF6347;
                    color: white;
                    font-size: 1.2rem;
                    padding: 0.5rem;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                }
                .random-button:hover {
                    background-color: #FF4500;
                }
                </style>
            """, unsafe_allow_html=True)
            
            if st.button("Choose Random Word"):
                if unique_chinese_words:
                    st.session_state['selected_word'] = random.choice(unique_chinese_words)
        
        with col3:
            input_word = st.text_input("Or input a new word:")
            if input_word:  # Automatically update selected_word when input changes
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
        
        # Create two columns with reversed order and vertical alignment
        col1, col2 = st.columns([2, 1])
        
        # Add vertical spacing to align with the word display
        with col1:
            generate_button_disabled = not st.session_state['selected_word']
            st.write("")  # Add some vertical spacing
            if st.button("Generate Sentence", disabled=generate_button_disabled):
                generate_sentence_for_app(st.session_state['selected_word'])
        
        with col2:
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
    
    except Exception as e:
        logger.error(f"Error in writing practice: {str(e)}")
        logger.error(traceback.format_exc())
        st.error(f"An error occurred: {str(e)}")

def generate_sentence_for_app(_word=None):
    """Generate a new sentence using SentenceGenerator."""
    try:
        sentence_generator = SentenceGenerator()
        result = sentence_generator.generate_sentence(_word if _word else "学习")
        
        if "error" in result:
            st.error(f"Error generating sentence: {result['error']}")
        else:
            # Ensure the result contains the necessary keys
            if all(key in result for key in ["english", "chinese", "pinyin"]):
                st.session_state['current_sentence'] = result
                # Store sentence in lang-portal if needed
                try:
                    sentence_generator.store_sentence(config.LANG_PORTAL_URL, result)
                except Exception as e:
                    st.warning(f"Could not store sentence in lang-portal: {e}")
            else:
                st.error("Error: Generated sentence does not contain all required keys.")
        return result
    except Exception as e:
        st.error(f"Error in generate_sentence_for_app: {e}")
        return {"error": str(e)}

def display_review(config_obj, reader):
    """Display the review and grading page."""
    # Grading and Review Stage
    st.markdown('<h1 class="main-header">Putonghua Learning App</h1>', unsafe_allow_html=True)
    
    # Add custom sentence input option
    st.markdown('<h2 class="sub-header">Review Options</h2>', unsafe_allow_html=True)
    use_custom_sentence = st.checkbox("Use custom sentence instead of generated sentence")
    
    if use_custom_sentence:
        # Initialize session state for custom inputs if they don't exist
        if 'custom_chinese' not in st.session_state:
            st.session_state.custom_chinese = ""
        if 'custom_english' not in st.session_state:
            st.session_state.custom_english = ""
        if 'custom_pinyin' not in st.session_state:
            st.session_state.custom_pinyin = ""

        # Previous values for change detection
        prev_chinese = st.session_state.custom_chinese
        prev_english = st.session_state.custom_english

        # Input fields with session state values
        custom_chinese = st.text_input("Enter Chinese characters:", 
                                     value=st.session_state.custom_chinese,
                                     key="custom_chinese_input")
        custom_english = st.text_input("Enter English translation:", 
                                     value=st.session_state.custom_english,
                                     key="custom_english_input")
        custom_pinyin = st.text_input("Enter Pinyin (optional):", 
                                    value=st.session_state.custom_pinyin,
                                    key="custom_pinyin_input")
        
        # Initialize sentence generator
        sentence_generator = SentenceGenerator()
        
        # Check which field was updated and generate translations
        if custom_english and custom_english != prev_english:
            try:
                with st.spinner("Generating translation..."):
                    result = sentence_generator.translate_english(custom_english)
                    if result and "error" not in result:
                        # Update session state
                        st.session_state.custom_chinese = result["chinese"]
                        st.session_state.custom_pinyin = result["pinyin"]
                        st.session_state.custom_english = custom_english
                        # Update the current sentence
                        st.session_state["current_sentence"] = {
                            "english": custom_english,
                            "chinese": result["chinese"],
                            "pinyin": result["pinyin"]
                        }
                        st.experimental_rerun()
                    else:
                        st.error("Failed to generate translation")
            except Exception as e:
                st.error(f"Error generating translation: {str(e)}")

        elif custom_chinese and custom_chinese != prev_chinese:
            try:
                with st.spinner("Generating translation..."):
                    result = sentence_generator.translate_chinese(custom_chinese)
                    if result and "error" not in result:
                        # Update session state
                        st.session_state.custom_english = result["english"]
                        st.session_state.custom_pinyin = result["pinyin"]
                        st.session_state.custom_chinese = custom_chinese
                        # Update the current sentence
                        st.session_state["current_sentence"] = {
                            "english": result["english"],
                            "chinese": custom_chinese,
                            "pinyin": result["pinyin"]
                        }
                        st.experimental_rerun()
                    else:
                        st.error("Failed to generate translation")
            except Exception as e:
                st.error(f"Error generating translation: {str(e)}")
        
        # Always update current_sentence with the latest values
        if custom_chinese or custom_english or custom_pinyin:
            st.session_state["current_sentence"] = {
                "chinese": custom_chinese,
                "english": custom_english,
                "pinyin": custom_pinyin
            }

    # Check if a sentence exists (either generated or custom)
    if not st.session_state.get("current_sentence") or "chinese" not in st.session_state["current_sentence"]:
        if not use_custom_sentence:
            st.info("Please go to the Writing Practice section and generate a sentence first before reviewing.")
            if st.button("Go to Writing Practice"):
                st.session_state['current_state'] = 'practice'
                st.experimental_rerun()
        else:
            st.info("Please enter both Chinese characters and English translation.")
    else:
        # Display current sentence information
        st.markdown(f'<div class="instruction-text">{st.session_state["current_sentence"]["english"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<h2 class="sub-header">Expected Chinese:</h2>', unsafe_allow_html=True)
        st.markdown(f'<div class="chinese-text">{st.session_state["current_sentence"]["chinese"]}</div>', unsafe_allow_html=True)
        if st.session_state["current_sentence"]["pinyin"]:
            st.markdown(f'<div class="pinyin-text">{st.session_state["current_sentence"]["pinyin"]}</div>', unsafe_allow_html=True)

        # Image upload section
        st.markdown('<h2 class="sub-header">Upload Your Writing</h2>', unsafe_allow_html=True)
        
        # Upload method selection
        upload_method = st.radio(
            "Choose upload method:",
            ["Traditional File Upload", "WSL File Path"],
            help="Choose 'WSL File Path' if you're running in Windows Subsystem for Linux"
        )

        col1, col2 = st.columns([3, 1])
        
        with col1:
            if upload_method == "Traditional File Upload":
                uploaded_file = st.file_uploader(
                    "Upload your image file",
                    type=["jpg", "jpeg", "png"],
                    help="Select an image file from your computer"
                )
                
                if st.button("Load Image", key="traditional_load"):
                    if uploaded_file is not None:
                        try:
                            st.session_state['uploaded_image'] = Image.open(uploaded_file)
                        except Exception as e:
                            st.error(f"Error loading image: {str(e)}")
                    else:
                        st.warning("Please select a file first")

            else:  # WSL File Path option
                st.markdown("""
                    <div class="instruction-text">
                    To upload your image using WSL:
                    1. Save your image file in an accessible location (e.g., /mnt/c/Users/YourName/Pictures/)
                    2. Enter the full path to your image file below
                    </div>
                """, unsafe_allow_html=True)

                file_path = st.text_input(
                    "Enter the full path to your image file:",
                    help="Example: /mnt/c/Users/YourName/Pictures/my_writing.jpg"
                )
                
                if st.button("Load Image", key="wsl_load"):
                    if file_path:
                        try:
                            st.session_state['uploaded_image'] = Image.open(file_path)
                        except Exception as e:
                            st.error(f"Error loading image: {str(e)}")
                            st.info("Make sure the file path is correct and the image format is supported (jpg, jpeg, or png)")
                    else:
                        st.warning("Please enter a file path first")

        # Display the uploaded image if it exists
        if 'uploaded_image' in st.session_state and st.session_state['uploaded_image'] is not None:
            st.image(st.session_state['uploaded_image'], caption="Your writing", use_column_width=True)

        # Grading section - Always visible
        st.markdown("### Grade Your Writing")
        grade_button_disabled = 'uploaded_image' not in st.session_state or st.session_state['uploaded_image'] is None
        if st.button("Grade My Writing", disabled=grade_button_disabled):
            if 'uploaded_image' in st.session_state and st.session_state['uploaded_image'] is not None:
                with st.spinner("Analyzing your writing..."):
                    # Get expected text before OCR processing
                    expected_text = st.session_state["current_sentence"]["chinese"]
                    
                    # Convert PIL Image to bytes for OCR
                    img_byte_arr = io.BytesIO()
                    st.session_state['uploaded_image'].save(img_byte_arr, format='PNG')
                    img_byte_arr = img_byte_arr.getvalue()
                    
                    try:
                        results = process_and_grade_image(img_byte_arr, expected_text)
                        
                        # Display results
                        if "error" in results:
                            st.error(f"Error processing image: {results['error']}")
                        else:
                            st.session_state['grading_results'] = results
                            
                            # Display grade
                            grade = results.get('grade', 'F')
                            accuracy = results.get('accuracy', 0)
                            
                            st.markdown(f"""
                                <h2 class="sub-header">Grading Results:</h2>
                                <div class="grade-{grade.lower()}">
                                    <span style="font-size: 48px;">Grade: {grade}</span>
                                    <span style="font-size: 24px; margin-left: 20px;">Accuracy: {accuracy}%</span>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Display comparison
                            st.markdown("<h3>Character Comparison:</h3>", unsafe_allow_html=True)
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("<h4>Expected:</h4>", unsafe_allow_html=True)
                                st.markdown(f'<div class="chinese-text">{expected_text}</div>', unsafe_allow_html=True)
                            
                            with col2:
                                st.markdown("<h4>Detected:</h4>", unsafe_allow_html=True)
                                st.markdown(f'<div class="chinese-text">{results.get("ocr_text", "")}</div>', unsafe_allow_html=True)
                            
                            # Feedback and tips
                            st.markdown("<h3>Feedback:</h3>", unsafe_allow_html=True)
                            
                            if grade in ['A', 'B']:
                                st.success("Great job! Your writing is clear and legible.")
                            elif grade == 'C':
                                st.warning("Your writing is readable but could use some improvement in clarity.")
                            else:
                                st.error("Your writing needs improvement. Focus on stroke order and character proportions.")
                            
                            # Tips based on accuracy
                            st.markdown("<h3>Tips for Improvement:</h3>", unsafe_allow_html=True)
                            
                            tips = [
                                "Practice writing characters with proper stroke order",
                                "Maintain consistent proportions within characters",
                                "Ensure adequate spacing between strokes",
                                "Write on grid paper to help with alignment",
                                "Slow down and focus on precision rather than speed"
                            ]
                            
                            for tip in tips:
                                st.markdown(f"- {tip}")
                    
                    except Exception as e:
                        st.error(f"Error during grading: {str(e)}")
                        logger.error(f"Error during grading: {str(e)}")
                        logger.error(traceback.format_exc())

def main():
    """Main application function."""
    logger.info("Starting WriteLab application")
    
    try:
        # Initialize configuration
        app_config = Config()
        
        # Check environment variables
        if not check_environment():
            st.error("Failed to initialize AWS configuration. Please check the logs.")
            return

        # Setup Streamlit
        if not setup_streamlit():
            st.error("Failed to initialize application. Please check the logs.")
            return

        # Initialize components
        reader = initialize_components()
        if reader is None:
            st.error("Failed to initialize components. Please check the logs.")
            return

        logger.info("Application initialized successfully")

        # Display sidebar for navigation
        display_sidebar(app_config)

        # Main app logic based on current state
        if st.session_state['current_state'] == 'setup':
            logger.debug("Entering setup state")
            if st.session_state['setup_state'] == 'word_collection':
                display_word_collection(app_config)
                
        elif st.session_state['current_state'] == 'practice':
            display_writing_practice(app_config, reader)
                
        elif st.session_state['current_state'] == 'review':
            display_review(app_config, reader)

    except Exception as e:
        logger.error(f"Unhandled exception in main: {str(e)}")
        logger.error(traceback.format_exc())
        st.error(f"""
            An unexpected error occurred. Please try again later.
            Error details have been logged.
            Error: {str(e)}
        """)

if __name__ == "__main__":
    main()