import sqlite3
import json
import os
from typing import List, Dict, Any
from contextlib import contextmanager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "songs.db"):
        """Initialize the database connection."""
        self.db_path = db_path
        self.conn = None
        self.ensure_connection()

    def ensure_connection(self):
        """Ensure that we have a database connection."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            # Enable foreign keys
            self.conn.execute("PRAGMA foreign_keys = ON")
            # Configure to return rows as dictionaries
            self.conn.row_factory = sqlite3.Row

    def create_tables(self):
        """Create the necessary tables if they don't exist."""
        self.ensure_connection()
        cursor = self.conn.cursor()
        
        # Create songs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id TEXT UNIQUE NOT NULL,
            artist TEXT,
            title TEXT,
            lyrics TEXT,
            vocabulary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create vocabulary table - updated column name from 'word' to 'jiantizi'
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id TEXT NOT NULL,
            jiantizi TEXT NOT NULL,
            pinyin TEXT,
            english TEXT,
            FOREIGN KEY (song_id) REFERENCES songs(song_id)
        )
        ''')

        # Create history table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            lyrics TEXT,
            vocabulary TEXT,
            timestamp TEXT DEFAULT (datetime('now', 'localtime'))
        )
        ''')
        
        self.conn.commit()
        logger.info("Database tables created successfully")

    def clear_history(self):
        """Clear all history entries."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM history')
            self.conn.commit()
            logger.info("History cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Error clearing history: {str(e)}")
            self.conn.rollback()
            return False

    def save_to_history(self, query: str, lyrics: str = None, vocab: str = None):
        """Save a query and its results to history."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Convert None to empty string and ensure all inputs are strings
                query = str(query) if query is not None else ""
                lyrics = str(lyrics) if lyrics is not None else ""
                vocab = str(vocab) if vocab is not None else ""
                
                cursor.execute(
                    'INSERT INTO history (query, lyrics, vocabulary) VALUES (?, ?, ?)',
                    (query, lyrics, vocab)
                )
                conn.commit()
                logger.info(f"Saved to history: {query}")
        except Exception as e:
            logger.error(f"Error saving to history: {str(e)}")

    def get_history(self):
        """Get all history entries."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute('SELECT query, lyrics, vocabulary, timestamp FROM history ORDER BY timestamp DESC')
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting history: {str(e)}")
            return []

    def save_song(self, song_id: str, artist: str, title: str, lyrics: str, vocabulary: List[Dict[str, Any]]):
        """
        Save a song and its vocabulary to the database.
        
        Args:
            song_id (str): The unique identifier for the song
            artist (str): The artist name
            title (str): The song title
            lyrics (str): The song lyrics
            vocabulary (List[Dict[str, Any]]): List of vocabulary items
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # Insert song
                cursor.execute(
                    "INSERT INTO songs (song_id, artist, title, lyrics) VALUES (?, ?, ?, ?)",
                    (song_id, artist, title, lyrics)
                )
                
                # Insert vocabulary
                for vocab in vocabulary:
                    cursor.execute(
                        """
                        INSERT INTO vocabulary (song_id, jiantizi, pinyin, english)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            song_id, 
                            vocab.get("jiantizi", ""),
                            vocab.get("pinyin", ""),
                            vocab.get("english", "")
                        )
                    )
                
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # Song already exists
                conn.rollback()
                return False
            except Exception as e:
                conn.rollback()
                raise e

    def get_song(self, song_id: str):
        """Get a song by its ID."""
        self.ensure_connection()
        cursor = self.conn.cursor()
        
        # Get song
        cursor.execute("SELECT * FROM songs WHERE song_id = ?", (song_id,))
        song = cursor.fetchone()
        
        if not song:
            return None
        
        # Get vocabulary
        cursor.execute("SELECT * FROM vocabulary WHERE song_id = ?", (song_id,))
        vocabulary = [dict(v) for v in cursor.fetchall()]
        
        return {
            "id": song["id"],
            "song_id": song["song_id"],
            "artist": song["artist"],
            "title": song["title"],
            "lyrics": song["lyrics"],
            "created_at": song["created_at"],
            "vocabulary": vocabulary
        }

    def get_song_history(self):
        """Get all songs with their vocabulary."""
        self.ensure_connection()
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT s.*, GROUP_CONCAT(json_object(
                'jiantizi', v.jiantizi,
                'pinyin', v.pinyin,
                'english', v.english
            )) as vocab_json
            FROM songs s
            LEFT JOIN vocabulary v ON s.song_id = v.song_id
            GROUP BY s.id
            ORDER BY s.created_at DESC
        """)
        
        results = []
        for row in cursor.fetchall():
            song_dict = dict(row)
            if song_dict['vocab_json']:
                song_dict['vocabulary'] = json.loads(f"[{song_dict['vocab_json']}]")
            else:
                song_dict['vocabulary'] = []
            del song_dict['vocab_json']
            results.append(song_dict)
        
        return results

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def initialize(self):
        """Initialize the database connection in the main thread"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Create your tables here
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS songs (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    artist TEXT,
                    lyrics TEXT,
                    vocabulary TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    @contextmanager
    def get_connection(self):
        """Get a thread-safe database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
        finally:
            conn.close()