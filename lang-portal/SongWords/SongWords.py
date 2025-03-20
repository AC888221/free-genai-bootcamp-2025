import streamlit as st
import pandas as pd
from typing import List, Dict
import logging
from tools.extract_vocabulary import extract_vocabulary
from tools.generate_song_id import generate_song_id
from agent import LyricsAgent
from database import Database
from tools.excluded_sites import ExcludedSitesTracker
from datetime import datetime
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
db = Database()
db.create_tables()

# Initialize agent and excluded sites tracker
agent = LyricsAgent()
excluded_sites = ExcludedSitesTracker()

def display_vocabulary(vocabulary_data, key_prefix=""):
    """Display vocabulary data in a table format.
    
    Args:
        vocabulary_data: List of dictionaries containing translations
        key_prefix: Prefix for Streamlit widget keys
    """
    if not vocabulary_data:
        st.warning("No vocabulary data available.")
        return
        
    try:
        # Create DataFrame directly from the list of dictionaries
        df = pd.DataFrame(vocabulary_data)
        
        # Rename columns if they exist
        column_mapping = {
            'original': 'Chinese',
            'pinyin': 'Pinyin',
            'english': 'English'
        }
        df = df.rename(columns=column_mapping)
        
        # Store DataFrame in session state
        state_key = f"{key_prefix}_vocabulary_df"
        if state_key not in st.session_state:
            st.session_state[state_key] = df
        
        # Display the table
        st.dataframe(st.session_state[state_key], use_container_width=True)
        
        # Create download button in a separate container
        col1, col2 = st.columns([4, 1])
        with col2:
            csv = st.session_state[state_key].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="vocabulary.csv",
                mime="text/csv",
                key=f"{key_prefix}_download_btn"
            )
            
    except Exception as e:
        st.error(f"Error displaying vocabulary: {str(e)}")
        logger.error(f"Error displaying vocabulary: {str(e)}", exc_info=True)

async def main():
    st.set_page_config(
        page_title="SongWords",
        page_icon="🎵",
        layout="wide"
    )
    
    st.title("🎵 SongWords")
    st.write("Search for Putonghua song lyrics and get vocabulary lists with pinyin and translations")
    
    # Create tabs for different functionalities
    tab1, tab2, tab3, tab4 = st.tabs(["Search", "Input Your Own", "History", "Excluded Sites"])
    
    with tab1:
        st.header("Search for Song Lyrics")
        st.info("Note: Processing may take a while as the AI analyzes the lyrics.")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            song_name = st.text_input("Song Name", placeholder="Enter song name", key="song_name")
        with col2:
            artist_name = st.text_input("Artist (Optional)", placeholder="Enter artist name", key="artist_name")
        
        if 'agent' not in st.session_state:
            st.session_state.agent = LyricsAgent()
            # Force database initialization in main thread
            st.session_state.agent.db.initialize()
        
        if st.button("Search", key="search_button"):
            if not song_name:
                st.error("Please enter a song name")
            else:
                with st.spinner("Searching for lyrics and extracting vocabulary..."):
                    try:
                        # Store results in session state
                        result = await st.session_state.agent.run(song_name, artist_name)
                        logger.info(f"Search button clicked. Result type: {type(result)}")
                        logger.info(f"Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
                        
                        if isinstance(result, dict):
                            st.session_state.search_result = result
                            
                            if "error" in result and result["error"]:
                                st.error(f"Error: {result['error']}")
                            else:
                                # Display lyrics
                                st.subheader("Lyrics")
                                lyrics = result.get("lyrics", "")
                                logger.info(f"Lyrics found (length: {len(lyrics)})")
                                st.text_area("", value=lyrics, height=300, disabled=True, 
                                           label_visibility="collapsed")
                                
                                # Display vocabulary
                                st.subheader("Vocabulary")
                                vocab = result.get("vocabulary", [])
                                logger.info(f"Vocabulary found. Type: {type(vocab)}")
                                logger.info(f"Vocabulary content: {vocab}")
                                
                                if vocab:
                                    st.info(f"Found {len(vocab)} vocabulary items")
                                    display_vocabulary(vocab, "search")
                                else:
                                    st.warning("No vocabulary items found")
                        else:
                            st.error("Invalid response format from agent")
                            logger.error(f"Invalid response format: {result}")
                            
                    except Exception as e:
                        logger.error(f"Error during search: {str(e)}", exc_info=True)
                        st.error(f"An error occurred: {str(e)}")
        
        # Display previous results if they exist in session state
        elif hasattr(st.session_state, 'search_result'):
            result = st.session_state.search_result
            logger.info("Displaying cached results")
            logger.info(f"Cached result type: {type(result)}")
            logger.info(f"Cached result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
            
            if isinstance(result, dict) and "error" not in result:
                st.subheader("Lyrics")
                lyrics = result.get("lyrics", "")
                logger.info(f"Displaying cached lyrics (length: {len(lyrics)})")
                st.text_area("", value=lyrics, height=300, disabled=True, 
                            label_visibility="collapsed")
                
                st.subheader("Vocabulary")
                vocab = result.get("vocabulary", [])
                logger.info(f"Displaying cached vocabulary. Type: {type(vocab)}")
                logger.info(f"Cached vocabulary content: {vocab}")
                
                if vocab:
                    st.info(f"Found {len(vocab)} cached vocabulary items")
                    display_vocabulary(vocab, "search")
                else:
                    st.warning("No vocabulary items found in cache")
    
    with tab2:
        # Input Your Own tab
        st.header("Input Your Own Text")
        user_text = st.text_area("Enter Putonghua text:", height=200)
        if st.button("Extract Vocabulary"):
            if user_text:
                with st.spinner("Extracting vocabulary..."):
                    try:
                        # Await the vocabulary extraction
                        simplified_text, translations = await extract_vocabulary(user_text)
                        st.subheader("Vocabulary")
                        if translations:
                            logger.info(f"Translations received: {translations}")
                            # Use the same display_vocabulary function
                            display_vocabulary(translations, "manual")
                            # Save to history with proper formatting
                            db.save_to_history("Manual Input", simplified_text, str(translations))
                        else:
                            st.warning("No vocabulary items found.")
                    except Exception as e:
                        st.error(f"An error occurred while extracting vocabulary: {str(e)}")
                        logger.error(f"Vocabulary extraction error: {str(e)}", exc_info=True)
            else:
                st.error("Please enter some text first.")

    with tab3:
        # History tab
        st.subheader("History")
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write("Previous lyrics and vocabulary results")
        with col2:
            if st.button("🔄 Refresh History"):
                st.rerun()
        with col3:
            if st.button("🗑️ Clear History"):
                if db.clear_history():
                    st.success("History cleared!")
                    st.rerun()
                else:
                    st.error("Failed to clear history")
            
        with st.container(border=True):
            try:
                history = db.get_history()
                if history:
                    for query, lyrics, vocab, timestamp in history:
                        with st.expander(f"{query} - {timestamp}", expanded=True):
                            if lyrics:
                                st.text("Lyrics:")
                                st.text(lyrics)
                            if vocab:
                                st.text("\nVocabulary:")
                                st.text(vocab)
                            if not lyrics and not vocab:
                                st.info("No results found")
                else:
                    st.info("No history yet")
            except Exception as e:
                st.error(f"Error loading history: {str(e)}")
                logger.error(f"Error loading history: {str(e)}")

    with tab4:
        # Excluded Sites tab
        st.subheader("Excluded Domains")
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write("Currently excluded domains and their status (includes all subdomains)")
        with col2:
            if st.button("🔄 Refresh Excluded Domains"):
                st.rerun()
        
        with st.container(border=True):
            report = excluded_sites.get_excluded_sites_report()
            if report:
                # Replace the "Individually blocked sites:" header in the report
                report = report.replace("Individually excluded sites:", "Excluded domains:")
                
                sections = report.split("\n\n")
                for section in sections:
                    if section.strip():
                        header = section.split('\n')[0]
                        with st.expander(header, expanded=True):
                            st.markdown("""
                            ℹ️ When a domain is excluded, all its subdomains are also excluded.
                            For example, excluding `example.com` also excludes `www.example.com` and `lyrics.example.com`
                            """)
                            st.text(section)
            else:
                st.info("No domains are currently excluded")

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
    asyncio.run(main()) 