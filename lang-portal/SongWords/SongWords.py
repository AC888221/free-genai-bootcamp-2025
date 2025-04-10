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
import ast
import re
from config import LANGUAGES, UI_CONFIG, LOG_CONFIG

# Configure logging
logging.basicConfig(**LOG_CONFIG)
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
        # Generate a unique key for this vocabulary data
        state_key = f"{key_prefix}_vocabulary_df"
        
        # Only create the DataFrame if it doesn't exist in session state
        if state_key not in st.session_state:
            # Normalize the vocabulary data to ensure consistent field names
            normalized_data = []
            for item in vocabulary_data:
                normalized_item = {
                    'Chinese': item.get('jiantizi', item.get('Chinese', '')),
                    'Pinyin': item.get('pinyin', item.get('Pinyin', '')),
                    'English': item.get('english', item.get('English', ''))
                }
                normalized_data.append(normalized_item)
            
            # Store DataFrame in session state
            st.session_state[state_key] = pd.DataFrame(normalized_data)
        
        # Create a container for the table and download button
        with st.container():
            # Display the table using the DataFrame from session state
            st.dataframe(
                st.session_state[state_key],
                use_container_width=True,
                hide_index=True,
                key=f"{key_prefix}_dataframe"
            )
            
            # Add download button with a callback
            csv = st.session_state[state_key].to_csv(index=False).encode('utf-8')
            
            # Column for download button to make it less prominent
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv,
                    file_name="vocabulary.csv",
                    mime="text/csv",
                    key=f"{key_prefix}_download_btn",
                    use_container_width=True,
                    help="Download vocabulary as CSV file"
                )
            
    except Exception as e:
        st.error(f"Error displaying vocabulary: {str(e)}")
        logger.error(f"Error displaying vocabulary: {str(e)}", exc_info=True)

async def main():
    st.set_page_config(
        page_title=UI_CONFIG["title"],
        page_icon=UI_CONFIG["icon"],
        layout=UI_CONFIG["layout"]
    )
    
    st.title(f"{UI_CONFIG['icon']} {UI_CONFIG['title']}")
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
        
        # Add a reload last search button
        if st.button("🔄 Reload Last Search", key="reload_last_search"):
            try:
                # Get the most recent search from history
                recent_history = db.get_most_recent_search(source='search')
                if recent_history:
                    query, lyrics, vocab_str, timestamp = recent_history
                    # Only proceed if we have both lyrics and vocabulary
                    if lyrics and vocab_str:
                        # Convert vocab string back to list of dictionaries
                        vocab_list = ast.literal_eval(vocab_str)
                        
                        # Store in session state
                        st.session_state.search_result = {
                            "lyrics": lyrics,
                            "vocabulary": vocab_list,
                            "success": True
                        }
                        st.success(f"Reloaded last search: {query}")
                        st.rerun()
                    else:
                        st.warning("Last search has incomplete data")
                else:
                    st.warning("No search history found")
            except Exception as e:
                st.error(f"Error reloading search: {str(e)}")
                logger.error(f"Error reloading search: {str(e)}", exc_info=True)
        
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
                                # Save to proper database tables
                                if "song_id" in result and result["song_id"]:
                                    # Save to songs and vocabulary tables
                                    db.save_song(
                                        result["song_id"],
                                        artist_name,
                                        song_name,
                                        result.get("lyrics", ""),
                                        result.get("vocabulary", [])
                                    )
                                    
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
        st.header("Input Your Own Text")
        
        user_text = st.text_area(
            "Enter Chinese text to analyze",
            height=150,
            placeholder="Paste your Chinese text here..."
        )
        
        # Add reload button for last manual extraction
        if st.button("🔄 Reload Last Extraction", key="reload_last_extraction"):
            try:
                recent_input = db.get_most_recent_search(source='input')
                if recent_input:
                    query, lyrics, vocab_str, timestamp = recent_input
                    if vocab_str:  # Only need vocabulary for display
                        vocab_list = ast.literal_eval(vocab_str)
                        
                        # Display the vocabulary
                        st.subheader("Vocabulary")
                        if vocab_list:
                            st.info(f"Found {len(vocab_list)} vocabulary items")
                            display_vocabulary(vocab_list, "manual")
                        else:
                            st.warning("No vocabulary items found")
                        st.success(f"Reloaded last extraction from: {timestamp}")
                    else:
                        st.warning("Last extraction has no vocabulary data")
                else:
                    st.warning("No previous extractions found")
            except Exception as e:
                st.error(f"Error reloading extraction: {str(e)}")
                logger.error(f"Error reloading extraction: {str(e)}", exc_info=True)
        
        if st.button("Extract Vocabulary", key="extract_button"):
            if user_text:
                with st.spinner("Extracting vocabulary..."):
                    try:
                        # Await the vocabulary extraction
                        simplified_text, translations = await extract_vocabulary(user_text)
                        st.subheader("Vocabulary")
                        if translations:
                            logger.info(f"Translations received: {translations}")
                            # Use the same display_vocabulary function with a different prefix
                            display_vocabulary(translations, "manual")
                            # Save to history with proper source
                            db.save_to_history("Manual Input", simplified_text, str(translations), source='input')
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
                    for query, lyrics, vocab, timestamp, source in history:
                        # Create an icon based on the source
                        source_icon = "🎵" if source == "search" else "📝"
                        source_label = "Song Search" if source == "search" else "Manual Input"
                        
                        with st.expander(f"{source_icon} {query} - {source_label} ({timestamp})", expanded=True):
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