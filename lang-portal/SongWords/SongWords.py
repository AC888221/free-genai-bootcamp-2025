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

def display_vocabulary(vocabulary, key_prefix=""):
    if vocabulary:
        try:
            # Convert vocabulary to a list of dictionaries if it isn't already
            if not isinstance(vocabulary, list):
                # Filter out None values and malformed entries
                valid_items = []
                for item in vocabulary:
                    try:
                        if item and len(item) >= 3:
                            valid_items.append({
                                'Jiantizi': item[0],
                                'Pinyin': item[1],
                                'English': item[2]
                            })
                    except (IndexError, TypeError):
                        continue  # Skip malformed entries
                vocabulary = valid_items
            
            if not vocabulary:
                st.warning("No valid vocabulary items could be extracted.")
                return
            
            # Create DataFrame
            df = pd.DataFrame(vocabulary)
            
            # Rename columns to sentence case if they exist
            if not df.empty and len(df.columns) == 3:
                df.columns = ['Jiantizi', 'Pinyin', 'English']
            
            # Display vocabulary in a table
            st.dataframe(df)
            
            # Add download button that won't trigger a rerun
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="vocabulary.csv",
                mime="text/csv",
                key=f"{key_prefix}_download_btn",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error processing vocabulary: {str(e)}")
            logger.error(f"Error processing vocabulary: {str(e)}")

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
                        st.session_state.search_result = await st.session_state.agent.run(song_name, artist_name)
                        
                        if "error" in st.session_state.search_result:
                            st.error(f"Error: {st.session_state.search_result['error']}")
                        else:
                            st.subheader("Lyrics")
                            st.text_area("", value=st.session_state.search_result.get("lyrics", ""), 
                                       height=300, disabled=True, label_visibility="collapsed")
                            st.subheader("Vocabulary")
                            display_vocabulary(st.session_state.search_result.get("vocabulary", []), "search")
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
        
        # Display previous results if they exist in session state
        elif hasattr(st.session_state, 'search_result'):
            if "error" not in st.session_state.search_result:
                st.subheader("Lyrics")
                st.text_area("", value=st.session_state.search_result.get("lyrics", ""), 
                            height=300, disabled=True, label_visibility="collapsed")
                st.subheader("Vocabulary")
                display_vocabulary(st.session_state.search_result.get("vocabulary", []), "search")
    
    with tab2:
        # Input Your Own tab
        st.header("Input Your Own Text")
        user_text = st.text_area("Enter Putonghua text:", height=200)
        if st.button("Extract Vocabulary"):
            if user_text:
                with st.spinner("Extracting vocabulary..."):
                    try:
                        # Await the vocabulary extraction
                        vocabulary = await extract_vocabulary(user_text)
                        st.subheader("Vocabulary")
                        if vocabulary:
                            # Use the same display_vocabulary function we fixed earlier
                            display_vocabulary(vocabulary, "manual")
                            # Save to history
                            db.save_to_history("Manual Input", user_text, str(vocabulary))
                        else:
                            st.warning("No vocabulary items found.")
                    except Exception as e:
                        st.error(f"An error occurred while extracting vocabulary: {str(e)}")
                        logger.error(f"Vocabulary extraction error: {str(e)}")
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