import streamlit as st
import requests
import random
import json
import pandas as pd
import io
import base64
from PIL import Image
from gtts import gTTS
import easyocr
import time
import numpy as np
import boto3
import os

# Set page config
st.set_page_config(
    page_title="Putonghua Learning App",
    page_icon="🀄",
    layout="centered"
)

# Initialize session state if needed
if 'current_state' not in st.session_state:
    st.session_state['current_state'] = 'setup'
if 'word_collection' not in st.session_state:
    st.session_state['word_collection'] = []
if 'current_sentence' not in st.session_state:
    st.session_state['current_sentence'] = {}
if 'grading_results' not in st.session_state:
    st.session_state['grading_results'] = {}

# Initialize OCR reader (cached as a resource)
@st.cache_resource
def load_ocr_reader():
    return easyocr.Reader(['ch_sim', 'en'])

reader = load_ocr_reader()

# Initialize Amazon Bedrock client
@st.cache_resource
def get_bedrock_client():
    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1",  # Change to your region
    )
    return bedrock_runtime

# Function to call Claude 3 Haiku on Amazon Bedrock
def call_claude_haiku(prompt, temperature=0.7, max_tokens=1000):
    client = get_bedrock_client()
    
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    response = client.invoke_model(
        modelId="anthropic.claude-3-haiku-20240307-v1:0",  # Claude 3 Haiku model ID
        body=json.dumps(request_body)
    )
    
    response_body = json.loads(response.get('body').read())
    return response_body.get('content')[0].get('text')

# Mock API function (replace with actual API call)
@st.cache_data(ttl=3600)
def fetch_word_collection():
    # In a real app, you would use:
    # response = requests.get("localhost:5000/api/groups/:id/raw")
    # return response.json()
    
    # For demo purposes, we'll use mock data
    return [
        {"chinese": "书", "english": "book", "pinyin": "shū"},
        {"chinese": "水", "english": "water", "pinyin": "shuǐ"},
        {"chinese": "吃", "english": "to eat", "pinyin": "chī"},
        {"chinese": "喝", "english": "to drink", "pinyin": "hē"},
        {"chinese": "去", "english": "to go", "pinyin": "qù"},
        {"chinese": "看", "english": "to look/see", "pinyin": "kàn"},
        {"chinese": "人", "english": "person", "pinyin": "rén"},
        {"chinese": "今天", "english": "today", "pinyin": "jīntiān"},
        {"chinese": "明天", "english": "tomorrow", "pinyin": "míngtiān"},
        {"chinese": "昨天", "english": "yesterday", "pinyin": "zuótiān"},
        {"chinese": "朋友", "english": "friend", "pinyin": "péngyou"},
        {"chinese": "家", "english": "home", "pinyin": "jiā"},
    ]

# Sentence generator function using Claude 3 Haiku
@st.cache_data(ttl=60)
def generate_sentence(_word):
    try:
        prompt = f"""
        Generate a simple sentence using the following Chinese word: {_word}
        The grammar should be scoped to HSK Level 1-2 grammar patterns.
        You can use the following vocabulary to construct a simple sentence:
        - Common objects (e.g., book/书, water/水, food/食物)
        - Basic verbs (e.g., to eat/吃, to drink/喝, to go/去)
        - Simple time expressions (e.g., today/今天, tomorrow/明天, yesterday/昨天)

        Return ONLY the following in JSON format:
        {{
          "english": "The English sentence",
          "chinese": "The Chinese sentence in simplified characters",
          "pinyin": "The pinyin representation with tone marks"
        }}
        """
        
        response = call_claude_haiku(prompt, temperature=0.3)
        
        # Find and extract the JSON part of the response
        response = response.strip()
        
        # Handle potential explanations or additional text before/after the JSON
        if response.find('{') >= 0 and response.rfind('}') >= 0:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            json_str = response[start_idx:end_idx]
            return json.loads(json_str)
        else:
            # Fallback if no JSON found
            return {
                "english": "I want to learn Chinese",
                "chinese": "我想学中文",
                "pinyin": "wǒ xiǎng xué zhōngwén"
            }
            
    except Exception as e:
        st.error(f"Error generating sentence: {str(e)}")
        # Fallback for errors
        return {
            "english": "I want to learn Chinese",
            "chinese": "我想学中文",
            "pinyin": "wǒ xiǎng xué zhōngwén"
        }

# Generate audio function
@st.cache_data(ttl=300)
def generate_audio(text):
    tts = gTTS(text, lang='zh-CN')
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)
    audio_bytes.seek(0)
    return audio_bytes

# OCR and grading function using Claude 3 Haiku
def process_and_grade_image(image, expected_chinese):
    # Process with OCR
    img_array = np.array(image)
    results = reader.readtext(img_array)
    
    # Extract text
    transcribed_text = " ".join([res[1] for res in results]) if results else "No text detected"
    
    try:
        # Use Claude 3 Haiku for translation and grading
        prompt = f"""
        I am analyzing a student's handwritten Chinese characters.

        Original English sentence: {st.session_state['current_sentence']['english']}
        Expected Chinese characters: {expected_chinese}
        OCR transcription of student's writing: {transcribed_text}

        Task 1: First, provide a literal English translation of the transcribed Chinese text.
        
        Task 2: Grade the student's writing based on how well it matches the expected Chinese characters.
        Use the S-A-B-C-D grading scale where:
        - S: Perfect match
        - A: Very good (>80% accuracy)
        - B: Good (>60% accuracy)
        - C: Needs improvement (>40% accuracy)
        - D: Significant errors (<40% accuracy)
        
        Task 3: Provide specific feedback on the characters and suggestions for improvement.

        Format your response as JSON:
        {{
          "back_translation": "English translation of transcribed text",
          "grade": "Grade letter (S/A/B/C/D)",
          "accuracy": decimal between 0-1,
          "feedback": "Specific feedback with suggestions"
        }}
        """
        
        response = call_claude_haiku(prompt, temperature=0.1)
        
        # Extract JSON from response
        response = response.strip()
        if response.find('{') >= 0 and response.rfind('}') >= 0:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            json_str = response[start_idx:end_idx]
            grading_result = json.loads(json_str)
        else:
            # Fallback if JSON extraction fails
            if transcribed_text == "No text detected":
                grading_result = {
                    "back_translation": "No text detected",
                    "grade": "D",
                    "accuracy": 0,
                    "feedback": "No Chinese characters were detected in the image. Please try again with clearer handwriting."
                }
            elif transcribed_text == expected_chinese:
                grading_result = {
                    "back_translation": st.session_state['current_sentence']['english'],
                    "grade": "S",
                    "accuracy": 1.0,
                    "feedback": "Perfect! Your characters match exactly what was expected."
                }
            else:
                grading_result = {
                    "back_translation": "Translation unavailable",
                    "grade": "C",
                    "accuracy": 0.5,
                    "feedback": "Some characters were recognized but there are errors. Keep practicing!"
                }
    
    except Exception as e:
        st.error(f"Error in grading: {str(e)}")
        # Fallback grading if API call fails
        if transcribed_text == "No text detected":
            grading_result = {
                "back_translation": "No text detected",
                "grade": "D",
                "accuracy": 0,
                "feedback": "No Chinese characters were detected in the image. Please try again with clearer handwriting."
            }
        elif transcribed_text == expected_chinese:
            grading_result = {
                "back_translation": st.session_state['current_sentence']['english'],
                "grade": "S",
                "accuracy": 1.0,
                "feedback": "Perfect! Your characters match exactly what was expected."
            }
        else:
            grading_result = {
                "back_translation": "Translation unavailable",
                "grade": "C",
                "accuracy": 0.5,
                "feedback": "Some characters were recognized but there are errors. Keep practicing!"
            }
    
    # Character comparison
    char_comparison = []
    for i, expected_char in enumerate(expected_chinese):
        if i < len(transcribed_text):
            is_correct = expected_char == transcribed_text[i]
            char_comparison.append({
                "expected": expected_char,
                "written": transcribed_text[i],
                "correct": is_correct
            })
        else:
            char_comparison.append({
                "expected": expected_char,
                "written": "",
                "correct": False
            })
    
    # Add any extra characters the user wrote
    for i in range(len(expected_chinese), len(transcribed_text)):
        char_comparison.append({
            "expected": "",
            "written": transcribed_text[i],
            "correct": False
        })
    
    # Combine results
    result = {
        "transcription": transcribed_text,
        "back_translation": grading_result.get("back_translation", "Translation unavailable"),
        "accuracy": grading_result.get("accuracy", 0.5),
        "grade": grading_result.get("grade", "C"),
        "feedback": grading_result.get("feedback", "Keep practicing!"),
        "char_comparison": char_comparison
    }
    
    return result

# Function to handle state transitions
def change_state(new_state):
    st.session_state['current_state'] = new_state
    if new_state == 'setup':
        # Reset everything
        st.session_state['current_sentence'] = {}
        st.session_state['grading_results'] = {}

# Generate new sentence
def generate_new_sentence():
    # Get word collection (fetch if not already in session)
    if not st.session_state['word_collection']:
        st.session_state['word_collection'] = fetch_word_collection()
    
    # Select random word
    random_word = random.choice(st.session_state['word_collection'])
    
    # Generate sentence
    with st.spinner("Generating sentence with Claude 3 Haiku..."):
        sentence_data = generate_sentence(random_word["chinese"])
    st.session_state['current_sentence'] = sentence_data
    
    # Change state to practice
    st.session_state['current_state'] = 'practice'

# Add some styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #FF4B4B;
        text-align: center;
    }
    .sub-header {
        font-size: 1.5rem;
        margin-bottom: 1rem;
    }
    .chinese-text {
        font-size: 2rem;
        color: #FF4B4B;
        margin: 1rem 0;
    }
    .pinyin-text {
        font-size: 1.2rem;
        color: #636EFA;
        margin-bottom: 1.5rem;
    }
    .instruction-text {
        font-size: 1rem;
        color: #7F7F7F;
        margin: 1rem 0;
    }
    .grade-s {color: #00CC96;}
    .grade-a {color: #636EFA;}
    .grade-b {color: #FFA15A;}
    .grade-c {color: #EF553B;}
    .grade-d {color: #AB63FA;}
    .char-correct {
        color: #00CC96;
        font-weight: bold;
    }
    .char-incorrect {
        color: #EF553B;
        text-decoration: line-through;
    }
    .stApp {
        max-width: 800px;
        margin: 0 auto;
    }
</style>
""", unsafe_allow_html=True)

# Add AWS credentials section (hidden by default)
with st.sidebar:
    st.header("AWS Configuration")
    with st.expander("AWS Credentials", expanded=False):
        aws_access_key = st.text_input("AWS Access Key ID", type="password")
        aws_secret_key = st.text_input("AWS Secret Access Key", type="password")
        aws_region = st.selectbox("AWS Region", 
                                  ["us-east-1", "us-west-1", "us-west-2", "eu-west-1", "ap-northeast-1"],
                                  index=0)
        
        if st.button("Save Credentials"):
            os.environ["AWS_ACCESS_KEY_ID"] = aws_access_key
            os.environ["AWS_SECRET_ACCESS_KEY"] = aws_secret_key
            os.environ["AWS_DEFAULT_REGION"] = aws_region
            st.success("AWS credentials saved for this session")
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This app uses:
    - Claude 3 Haiku on Amazon Bedrock
    - EasyOCR for character recognition
    - Google TTS for pronunciation
    
    Created for language learning bootcamp.
    """)

# Main app logic based on current state
if st.session_state['current_state'] == 'setup':
    # Setup State
    st.markdown('<h1 class="main-header">Putonghua Learning App</h1>', unsafe_allow_html=True)
    st.markdown("""
    Welcome to the Putonghua Learning App! This app will help you practice writing Chinese characters.
    
    Press the button below to get started with a random Chinese sentence.
    
    #### Before starting:
    Make sure to enter your AWS credentials in the sidebar if you haven't already.
    """)
    
    if st.button("Generate Sentence", use_container_width=True):
        generate_new_sentence()
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
        if st.button("Submit for Review", use_container_width=True):
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
        if st.button("Try Again", use_container_width=True):
            st.session_state['current_state'] = 'practice'
            st.session_state['grading_results'] = {}
            st.experimental_rerun()
    
    with col2:
        if st.button("New Sentence", use_container_width=True):
            generate_new_sentence()
            st.experimental_rerun()