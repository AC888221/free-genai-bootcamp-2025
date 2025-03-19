import streamlit as st
import pandas as pd
from typing import List, Dict
import logging
from tools.extract_vocabulary import extract_vocabulary
from tools.lyrics_extractor import get_lyrics
from tools.generate_song_id import generate_song_id
from agent import LyricsAgent
from database import Database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def display_vocabulary(vocabulary: List[Dict[str, str]], key_suffix: str = ""):
    """Display vocabulary in a nice format."""
    if not vocabulary:
        st.warning("No vocabulary items found.")
        return
    
    df = pd.DataFrame(vocabulary)
    if all(col in df.columns for col in ["word", "jiantizi", "pinyin", "english"]):
        df = df[["word", "jiantizi", "pinyin", "english"]]
    
    st.dataframe(df, use_container_width=True)
    
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download Vocabulary as CSV",
        data=csv,
        file_name="vocabulary.csv",
        mime="text/csv",
        key=f"download_btn_{key_suffix}"
    )

async def main():
    st.set_page_config(
        page_title="SongWords",
        page_icon="🎵",
        layout="wide"
    )
    
    st.title("🎵 SongWords")
    st.markdown("""
    This application helps you learn Putonghua by extracting vocabulary from songs. 
    You can search for song lyrics or input your own text to extract vocabulary.
    """)
    
    # Create tabs for different functionalities
    tab1, tab2, tab3 = st.tabs(["Search for Lyrics", "Input Your Own", "History"])
    
    with tab1:
        st.header("Search for Song Lyrics")
        st.info("Note: Processing may take a few seconds as the AI analyzes the lyrics.")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            song_name = st.text_input("Song Name", placeholder="Enter song name")
        with col2:
            artist_name = st.text_input("Artist (Optional)", placeholder="Enter artist name")
        
        if 'agent' not in st.session_state:
            st.session_state.agent = LyricsAgent()
            # Force database initialization in main thread
            st.session_state.agent.db.initialize()
        
        if st.button("Search", key="search_button"):
            if not song_name:
                st.error("Please enter a song name")
            else:
                with st.spinner("Searching for lyrics and extracting vocabulary..."):
                    result = await st.session_state.agent.run(song_name, artist_name)
                
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    # Display lyrics
                    st.subheader("Lyrics")
                    st.text_area("", value=result.get("lyrics", ""), height=300, disabled=True)
                    
                    # Display vocabulary
                    st.subheader("Vocabulary")
                    display_vocabulary(result.get("vocabulary", []), "search")
    
    with tab2:
        st.header("Input Your Own Song Lyrics")
        st.info("Note: Processing may take a some time as the AI analyzes the text.")
        
        text_input = st.text_area("Enter Putonghua text", height=300, placeholder="Paste Putonghua text here...")
        
        if st.button("Extract Vocabulary", key="extract_button"):
            if not text_input:
                st.error("Please enter some text")
            else:
                with st.spinner("Extracting vocabulary..."):
                    result = extract_vocabulary(text_input)
                
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    st.subheader("Extracted Vocabulary")
                    display_vocabulary(result.get("vocabulary", []), "extract")

    with tab3:
        st.header("Search History")
        if 'agent' in st.session_state:
            try:
                # Create a new connection for this operation
                with st.session_state.agent.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM songs ORDER BY timestamp DESC")
                    history = [
                        {
                            'title': row[1],
                            'artist': row[2],
                            'lyrics': row[3],
                            'vocabulary': eval(row[4])  # Assuming vocabulary is stored as string
                        }
                        for row in cursor.fetchall()
                    ]
                    
                for i, song in enumerate(history):
                    with st.expander(f"{song['title']} - {song['artist']}"):
                        st.text(song['lyrics'])
                        display_vocabulary(song['vocabulary'], f"history_{i}")
            except Exception as e:
                st.error(f"Error loading history: {str(e)}")

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
    import asyncio
    asyncio.run(main()) 