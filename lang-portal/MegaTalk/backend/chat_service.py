import json
import time
import sys
import os
import uuid
from typing import Tuple, Optional, Dict, Any
import sqlite3
from datetime import datetime

# Add the parent directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.config import (
    logger, MAX_HISTORY_LENGTH
)
from backend.prompts import get_summary_prompt
from backend.bedrock_client import call_bedrock_model
from backend.polly_client import call_polly_tts

# Database setup
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "chat_history.db")

def init_db():
    """Initialize the database with necessary tables."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                session_id TEXT,
                role TEXT,
                content TEXT,
                audio_path TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE
            )
        """)
        conn.commit()

def create_or_get_session() -> str:
    """Create a new chat session."""
    with sqlite3.connect(DB_PATH) as conn:
        session_id = str(uuid.uuid4())
        conn.execute("INSERT INTO sessions (session_id) VALUES (?)", (session_id,))
        conn.commit()
        return session_id

def save_message(session_id: str, role: str, content: str, audio_path: Optional[str] = None) -> str:
    """Save a message to the database."""
    # Extract just the user message if it's a user message with full prompt
    if role == "user" and "User: " in content:
        content = content.split("User: ")[-1]

    with sqlite3.connect(DB_PATH) as conn:
        message_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO messages (message_id, session_id, role, content, audio_path) VALUES (?, ?, ?, ?, ?)",
            (message_id, session_id, role, content, audio_path)
        )
        conn.execute(
            "UPDATE sessions SET last_updated = CURRENT_TIMESTAMP WHERE session_id = ?",
            (session_id,)
        )
        conn.commit()
        return message_id

def get_conversation_history(session_id: str, limit: int = MAX_HISTORY_LENGTH) -> list:
    """Retrieve recent conversation history for a session."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            SELECT role, content 
            FROM messages 
            WHERE session_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (session_id, limit))
        return list(reversed(cursor.fetchall()))

def summarize_conversation(session_id: str) -> str:
    """Generate a summary of the conversation using the LLM."""
    history = get_conversation_history(session_id, MAX_HISTORY_LENGTH)
    conversation_text = "\n".join([f"{role}: {content}" for role, content in history])
    
    # Get summary from LLM using prompt from prompts.py
    summary_prompt = get_summary_prompt(conversation_text)
    summary = call_bedrock_model(summary_prompt)
    
    # Save summary as a special system message
    save_message(session_id, "system", f"Conversation Summary: {summary}")
    
    return summary

def generate_prompt_with_history(session_id: str, user_prompt: str) -> str:
    """Generate a complete prompt including conversation history and summary."""
    history = get_conversation_history(session_id)
    
    # Find the most recent summary and its position in history
    summary = None
    summary_index = -1
    for i, (role, content) in enumerate(history):
        if role == "system" and content.startswith("Conversation Summary:"):
            summary = content
            summary_index = i
            break
    
    complete_prompt = ""
    if summary:
        # Add the summary
        complete_prompt += f"{summary}\n\n"
        # Only add messages that occurred after the summary
        recent_messages = history[summary_index + 1:]
        if recent_messages:
            complete_prompt += "Recent messages:\n"
            for role, content in recent_messages:
                complete_prompt += f"{role}: {content}\n"
    else:
        # If no summary exists, include last few messages
        recent_messages = history[-5:]
        if recent_messages:
            complete_prompt += "Recent messages:\n"
            for role, content in recent_messages:
                complete_prompt += f"{role}: {content}\n"
    
    # Add the current user prompt
    complete_prompt += f"\nCurrent message:\nUser: {user_prompt}"
    
    return complete_prompt

def get_chat_response(
    prompt: str,
    session_id: Optional[str] = None,
    config_params: Dict[str, Any] = {}
) -> Tuple[str, Optional[bytes], Optional[str], dict]:
    """Get response from the language model and save to database."""
    try:
        # Create or get session
        if not session_id:
            session_id = create_or_get_session()

        # Check if we need to summarize the conversation
        history = get_conversation_history(session_id)
        if len(history) >= MAX_HISTORY_LENGTH:
            summarize_conversation(session_id)
        
        # Generate complete prompt with history
        full_prompt = generate_prompt_with_history(session_id, prompt)

        # Save user message
        user_message_id = save_message(session_id, "user", prompt)
        
        # Get text response from Bedrock
        response_text = call_bedrock_model(full_prompt)
        if not response_text:
            logger.error("No response text received from Bedrock")
            return "", None, "Failed to get response from language model", {}

        # Generate message ID for assistant's response
        assistant_message_id = str(uuid.uuid4())

        # Generate audio if requested
        audio_data = None
        audio_path = None
        if config_params.get("generate_audio"):
            try:
                audio_data, audio_path = call_polly_tts(
                    response_text,
                    session_id,
                    assistant_message_id,
                    voice_id=config_params.get("voice", "Zhiyu")
                )
                if not audio_data:
                    logger.error("No audio data received from Polly")
            except Exception as e:
                logger.error(f"TTS generation failed: {str(e)}")

        # Save assistant's response
        save_message(session_id, "assistant", response_text, audio_path)
                
        response_details = {
            "timestamp": time.time(),
            "prompt_length": len(prompt),
            "response_length": len(response_text) if response_text else 0,
            "audio_generated": audio_data is not None,
            "session_id": session_id
        }
        logger.info(f"Response Details: {response_details}")
        
        return response_text, audio_data, None, response_details
        
    except Exception as e:
        logger.error(f"Service error: {str(e)}")
        return "", None, f"Service error: {str(e)}", {}

# Initialize database when module is loaded
init_db()