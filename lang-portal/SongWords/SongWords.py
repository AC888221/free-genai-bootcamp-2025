import streamlit as st
import pandas as pd
from typing import List, Dict
import logging
from tools.extract_vocabulary import extract_vocabulary
from tools.generate_song_id import generate_song_id
from agent import LyricsAgent
from database import Database
from tools.blocked_sites import BlockedSitesTracker
from datetime import datetime
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
db = Database()
db.create_tables()

# Initialize agent and blocked sites tracker
agent = LyricsAgent()
blocked_sites = BlockedSitesTracker()

def display_vocabulary(vocabulary, key_prefix=""):
    if vocabulary:
        # Create DataFrame
        df = pd.DataFrame(vocabulary)
        
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

async def main():
    st.set_page_config(
        page_title="SongWords",
        page_icon="🎵",
        layout="wide"
    )
    
    st.title("SongWords - Chinese Lyrics Search")
    
    # Create tabs for different functionalities
    tab1, tab2, tab3, tab4 = st.tabs(["Search", "Input Your Own", "History", "Blocked Sites"])
    
    with tab1:
        st.header("Search for Song Lyrics")
        st.info("Note: Processing may take a few seconds as the AI analyzes the lyrics.")
        
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
        user_text = st.text_area("Enter Chinese text:", height=200)
        if st.button("Extract Vocabulary"):
            if user_text:
                with st.spinner("Extracting vocabulary..."):
                    vocabulary = extract_vocabulary(user_text)
                    st.subheader("Vocabulary")
                    if vocabulary:
                        # Display vocabulary
                        df = pd.DataFrame(vocabulary)
                        st.dataframe(df)
                        # Save to history
                        db.save_to_history("Manual Input", user_text, str(vocabulary))
                    else:
                        st.warning("No vocabulary items found.")
            else:
                st.error("Please enter some text first.")

    with tab3:
        # History tab
        st.subheader("Search History")
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write("Previous searches and their results")
        with col2:
            if st.button("🔄 Refresh History"):
                st.rerun()
            
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
                                st.info("Search failed or no results found")
                else:
                    st.info("No search history yet")
            except Exception as e:
                st.error(f"Error loading history: {str(e)}")
                logger.error(f"Error loading history: {str(e)}")

    with tab4:
        # Blocked Sites tab
        st.subheader("Blocked Sites Status")
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write("Currently blocked sites and their status")
        with col2:
            if st.button("🔄 Refresh Blocked Sites"):
                st.rerun()
        
        with st.container(border=True):
            report = blocked_sites.get_blocked_sites_report()
            if report:
                sections = report.split("\n\n")
                for section in sections:
                    if section.strip():
                        header = section.split('\n')[0]
                        with st.expander(header, expanded=True):
                            st.text(section)
            else:
                st.info("No sites are currently blocked")

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