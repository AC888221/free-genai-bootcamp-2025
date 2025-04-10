import sqlite3
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
from datetime import datetime
import logging
import threading
from config import DB_PATH, LOG_CONFIG
import time

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path=None):
        # Use the config DB_PATH as default, allow override for testing
        self.db_path = db_path if db_path is not None else DB_PATH
        self._local = threading.local()
        self.logger = logging.getLogger(__name__)
        self.create_tables()

    @property
    def conn(self):
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(self.db_path)
            # Enable foreign key support
            self._local.conn.execute("PRAGMA foreign_keys = ON")
        return self._local.conn

    def ensure_connection(self):
        """Ensure we have a valid connection for the current thread."""
        try:
            # Test the connection
            self.conn.cursor()
        except (sqlite3.Error, AttributeError):
            # If there's an error, create a new connection
            self._local.conn = sqlite3.connect(self.db_path)

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

        # Create history table with source field
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            lyrics TEXT,
            vocabulary TEXT,
            source TEXT CHECK(source IN ('search', 'input')),
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
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

    def save_to_history(self, query: str, lyrics: str, vocabulary: str, source: str = 'search'):
        """Save a search query and its results to history."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO history (query, lyrics, vocabulary, source) VALUES (?, ?, ?, ?)",
                    (query, lyrics, vocabulary, source)
                )
                self.logger.info(f"Saved to history: {query}")
            except Exception as e:
                self.logger.error(f"Error saving to history: {str(e)}")
                raise

    def get_history(self) -> List[Tuple[str, str, str, str, str]]:
        """Get all search history."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT query, lyrics, vocabulary, timestamp, source 
                    FROM history 
                    ORDER BY timestamp DESC
                """)
                return cursor.fetchall()
            except Exception as e:
                self.logger.error(f"Error getting history: {str(e)}")
                return []

    def get_most_recent_search(self, source: str) -> Optional[Tuple[str, str, str, str]]:
        """Get the most recent entry from history for a specific source."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT query, lyrics, vocabulary, timestamp 
                    FROM history 
                    WHERE source = ?
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """, (source,))
                result = cursor.fetchone()
                return result if result else None
            except Exception as e:
                self.logger.error(f"Error getting most recent search: {str(e)}")
                return None

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
        columns = [desc[0] for desc in cursor.description]
        vocabulary = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
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
            # Convert row to dictionary using column names
            columns = [desc[0] for desc in cursor.description]
            song_dict = dict(zip(columns, row))
            
            # Parse vocabulary JSON if present
            if song_dict.get('vocab_json'):
                song_dict['vocabulary'] = json.loads(f"[{song_dict['vocab_json']}]")
            else:
                song_dict['vocabulary'] = []
            del song_dict['vocab_json']
            results.append(song_dict)
        
        return results

    def close(self):
        """Close the database connection."""
        if hasattr(self._local, "conn"):
            self._local.conn.close()
            delattr(self._local, "conn")

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
        """Context manager to handle database connections per thread."""
        self.ensure_connection()
        try:
            yield self.conn
        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            self.conn.commit()

def test_get_most_recent_search(db):
    # Fixed version:
    time.sleep(1)  # Use full second intervals