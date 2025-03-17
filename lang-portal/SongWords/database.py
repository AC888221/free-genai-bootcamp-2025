import sqlite3
import json
import os
from typing import List, Dict, Any

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
            artist TEXT NOT NULL,
            title TEXT NOT NULL,
            lyrics TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create vocabulary table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id TEXT NOT NULL,
            word TEXT NOT NULL,
            jiantizi TEXT NOT NULL,
            pinyin TEXT NOT NULL,
            english TEXT NOT NULL,
            FOREIGN KEY (song_id) REFERENCES songs(song_id),
            UNIQUE(song_id, word)
        )
        ''')
        
        self.conn.commit()

    def save_song(self, artist: str, title: str, lyrics: str, vocabulary: List[Dict[str, Any]]):
        """Save a song and its vocabulary to the database."""
        from tools.generate_song_id import generate_song_id
        
        self.ensure_connection()
        cursor = self.conn.cursor()
        
        # Generate a unique song_id
        song_id = generate_song_id(artist, title)
        
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
                    INSERT INTO vocabulary (song_id, word, jiantizi, pinyin, english)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        song_id, 
                        vocab.get("word", ""),
                        vocab.get("jiantizi", ""),
                        vocab.get("pinyin", ""),
                        vocab.get("english", "")
                    )
                )
            
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Song already exists
            self.conn.rollback()
            return False
        except Exception as e:
            self.conn.rollback()
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
                'word', v.word,
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