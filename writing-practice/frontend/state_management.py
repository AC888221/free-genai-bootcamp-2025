import streamlit as st
import random
import logging
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from word_collection import fetch_word_collection
from sentence_generation import generate_sentence

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def change_state(new_state):
    try:
        st.session_state['current_state'] = new_state
        if new_state == 'setup':
            # Reset everything
            st.session_state['current_sentence'] = {}
            st.session_state['grading_results'] = {}
        logging.info(f"State changed to {new_state}")
    except Exception as e:
        logging.error(f"Error changing state: {e}")
        st.error(f"An error occurred while changing state: {e}")

def generate_new_sentence():
    try:
        # Get word collection (fetch if not already in session)
        if 'word_collection' not in st.session_state or not st.session_state['word_collection']:
            st.session_state['word_collection'] = fetch_word_collection()
        
        # Select random word
        random_word = random.choice(st.session_state['word_collection'])
        
        # Generate sentence
        with st.spinner("Generating sentence with Claude 3 Haiku..."):
            sentence_data = generate_sentence(random_word["chinese"])
        st.session_state['current_sentence'] = sentence_data
        
        # Change state to practice
        st.session_state['current_state'] = 'practice'
        logging.info("New sentence generated and state changed to practice")
    except KeyError as e:
        logging.error(f"KeyError: {e}")
        st.error(f"An error occurred while generating a new sentence: {e}")
    except Exception as e:
        logging.error(f"Error generating new sentence: {e}")
        st.error(f"An error occurred while generating a new sentence: {e}")