import sqlite3
import os
from typing import List, Dict, Optional
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "chat_history.db")

def get_all_sessions() -> List[Dict]:
    """Retrieve all chat sessions."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT session_id, created_at, last_updated 
            FROM sessions 
            ORDER BY last_updated DESC
        """)
        return [dict(row) for row in cursor.fetchall()]

def get_session_messages(session_id: str) -> List[Dict]:
    """Retrieve all messages for a given session."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT message_id, role, content, audio_path, timestamp 
            FROM messages 
            WHERE session_id = ? 
            ORDER BY timestamp
        """, (session_id,))
        return [dict(row) for row in cursor.fetchall()]

def delete_session(session_id: str) -> bool:
    """Delete a session and its associated messages and audio files."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # First get all audio paths to delete files
            cursor = conn.execute("""
                SELECT audio_path FROM messages 
                WHERE session_id = ? AND audio_path IS NOT NULL
            """, (session_id,))
            audio_paths = [row[0] for row in cursor.fetchall()]
            
            # Delete messages and session from database
            # Note: CASCADE will automatically delete associated messages
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            
            # Delete audio files
            for path in audio_paths:
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError as e:
                        logger.error(f"Error deleting audio file {path}: {e}")
            
            return True
    except Exception as e:
        print(f"Error deleting session: {e}")
        return False

if __name__ == "__main__":
    # Test database utilities
    print("\nTesting database utilities...")
    sessions = get_all_sessions()
    print(f"\nFound {len(sessions)} sessions")
    for session in sessions:
        print(f"\nSession ID: {session['session_id']}")
        print(f"Created: {session['created_at']}")
        print(f"Last Updated: {session['last_updated']}")
        
        messages = get_session_messages(session['session_id'])
        print(f"Messages in session ({len(messages)} total):")
        for msg in messages:
            print(f"- {msg['role']}: {msg['content'][:50]}...")
            if msg['audio_path']:
                print(f"  Audio: {msg['audio_path']}") 