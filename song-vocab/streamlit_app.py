import streamlit as st
import httpx
import json
import pandas as pd
from typing import List, Dict, Any
import os
import logging
import asyncio
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API endpoint (adjust if needed)
API_BASE_URL = "http://localhost:8000"

# Increase timeout significantly for LLM operations
TIMEOUT_SECONDS = 300.0

async def get_lyrics(song_name: str, artist_name: str = None) -> Dict[str, Any]:
    """Call the API to get lyrics and vocabulary."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            # Format the request exactly as expected by the backend
            request_data = {
                "message_request": song_name
            }
            if artist_name:
                request_data["artist_name"] = artist_name
                
            logger.info(f"Sending request to /api/agent: {request_data}")
            
            response = await client.post(
                f"{API_BASE_URL}/api/agent",
                json=request_data
            )
            logger.info(f"Response status code: {response.status_code}")
            
            # Try to log response content even if it's not valid JSON
            try:
                response_text = response.text
                logger.info(f"Response content (first 200 chars): {response_text[:200]}...")
            except Exception as e:
                logger.error(f"Could not log response content: {str(e)}")
            
            response.raise_for_status()
            return response.json()
    except httpx.ReadTimeout:
        logger.error("Request timed out after waiting for response")
        return {
            "error": f"Request timed out after {TIMEOUT_SECONDS} seconds. The LLM processing may be taking longer than expected. Please try again or try with a shorter text."
        }
    except httpx.ConnectError:
        logger.error(f"Error connecting to backend API at {API_BASE_URL}")
        return {"error": f"Could not connect to the backend API at {API_BASE_URL}. Please make sure the backend server is running."}
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {str(e)}")
        logger.error(f"Response status code: {e.response.status_code}")
        try:
            error_content = e.response.text
            logger.error(f"Error response content: {error_content}")
            return {"error": f"HTTP error {e.response.status_code}: {error_content}"}
        except:
            return {"error": f"HTTP error {e.response.status_code}"}
    except Exception as e:
        logger.error(f"Error getting lyrics: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"error": str(e)}

async def get_vocabulary_from_text(text: str) -> Dict[str, Any]:
    """Call the API to extract vocabulary from text."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            # Format the request exactly as expected by the backend
            request_data = {"text": text}
            logger.info(f"Sending request to /api/get_vocabulary: {request_data}")
            
            response = await client.post(
                f"{API_BASE_URL}/api/get_vocabulary",
                json=request_data
            )
            logger.info(f"Response status code: {response.status_code}")
            
            # Try to log response content even if it's not valid JSON
            try:
                response_text = response.text
                logger.info(f"Response content (first 200 chars): {response_text[:200]}...")
            except Exception as e:
                logger.error(f"Could not log response content: {str(e)}")
                
            response.raise_for_status()
            return response.json()
    except httpx.ReadTimeout:
        logger.error("Request timed out after waiting for response")
        return {
            "error": f"Request timed out after {TIMEOUT_SECONDS} seconds. The LLM processing may be taking longer than expected. Please try again or try with a shorter text."
        }
    except httpx.ConnectError:
        logger.error(f"Error connecting to backend API at {API_BASE_URL}")
        return {"error": f"Could not connect to the backend API at {API_BASE_URL}. Please make sure the backend server is running."}
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {str(e)}")
        logger.error(f"Response status code: {e.response.status_code}")
        try:
            error_content = e.response.text
            logger.error(f"Error response content: {error_content}")
            return {"error": f"HTTP error {e.response.status_code}: {error_content}"}
        except:
            return {"error": f"HTTP error {e.response.status_code}"}
    except Exception as e:
        logger.error(f"Error extracting vocabulary: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"error": str(e)}

def run_async(func, *args, **kwargs):
    """Run an async function from Streamlit."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(func(*args, **kwargs))
    loop.close()
    return result

def display_vocabulary(vocabulary: List[Dict[str, str]]):
    """Display vocabulary in a nice format."""
    if not vocabulary:
        st.warning("No vocabulary items found.")
        return
    
    # Create a DataFrame for better display
    df = pd.DataFrame(vocabulary)
    
    # Reorder columns if needed
    if all(col in df.columns for col in ["word", "jiantizi", "pinyin", "english"]):
        df = df[["word", "jiantizi", "pinyin", "english"]]
    
    # Display the vocabulary table
    st.dataframe(df, use_container_width=True)
    
    # Add download button for CSV
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download Vocabulary as CSV",
        data=csv,
        file_name="vocabulary.csv",
        mime="text/csv"
    )

def main():
    st.set_page_config(
        page_title="Putonghua Song Vocabulary",
        page_icon="🎵",
        layout="wide"
    )
    
    st.title("🎵 Putonghua Song Vocabulary")
    st.markdown("""
    This application helps you learn Putonghua by extracting vocabulary from songs. 
    You can search for song lyrics or input your own text to extract vocabulary.
    """)
    
    # Create tabs for different functionalities
    tab1, tab2 = st.tabs(["Search for Lyrics", "Input Your Own"])
    
    with tab1:
        st.header("Search for Song Lyrics")
        st.info("Note: Processing may take up to 5 minutes as the AI analyzes the lyrics.")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            song_name = st.text_input("Song Name", placeholder="Enter song name")
        with col2:
            artist_name = st.text_input("Artist (Optional)", placeholder="Enter artist name")
        
        if st.button("Search", key="search_button"):
            if not song_name:
                st.error("Please enter a song name")
            else:
                with st.spinner("Searching for lyrics and extracting vocabulary... (This may take up to 5 minutes)"):
                    result = run_async(get_lyrics, song_name, artist_name)
                
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    # Display lyrics
                    st.subheader("Lyrics")
                    st.markdown(f"Source: {result.get('source', 'Unknown')}")
                    st.text_area("", value=result.get("lyrics", ""), height=300, disabled=True)
                    
                    # Display vocabulary
                    st.subheader("Vocabulary")
                    display_vocabulary(result.get("vocabulary", []))
    
    with tab2:
        st.header("Input Your Own Song Lyrics")
        st.info("Note: Processing may take up to 2 minutes as the AI analyzes the text.")
        
        text_input = st.text_area("Enter Putonghua text", height=300, placeholder="Paste Putonghua text here...")
        
        if st.button("Extract Vocabulary", key="extract_button"):
            if not text_input:
                st.error("Please enter some text")
            else:
                with st.spinner("Extracting vocabulary... (This may take up to 2 minutes)"):
                    result = run_async(get_vocabulary_from_text, text_input)
                
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    st.subheader("Extracted Vocabulary")
                    display_vocabulary(result.get("vocabulary", []))

    # Add information about the application
    st.sidebar.title("Features")
    st.sidebar.info("""
    - Search for song lyrics
    - Extract vocabulary with pinyin and translations
    - Process custom text input
    - Download vocabulary as CSV
    """)
    
    # Add a section about learning Putonghua
    st.sidebar.title("Putonghua Learning Tips")
    st.sidebar.markdown("""
    - Listen to songs repeatedly to improve pronunciation
    - Practice writing characters to reinforce memory
    - Use the vocabulary in sentences
    - Study the tones carefully - they change meaning!
    """)

if __name__ == "__main__":
    main() 