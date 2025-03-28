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
    logger, MAX_UNSUMMARIZED_TOKENS,
    CHARS_PER_TOKEN, SUMMARY_SECTION_HEADER, NEW_MESSAGES_SECTION_HEADER
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

def get_conversation_history(session_id: str, limit: int = MAX_UNSUMMARIZED_TOKENS) -> list:
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

def get_unsummarized_messages(session_id: str) -> Tuple[list, Optional[str]]:
    """Get messages that haven't been included in any summary and the last summary."""
    history = get_conversation_history(session_id)
    last_summary = None
    last_summary_index = -1
    
    # Find the last summary's position and content
    for i, (role, content) in enumerate(history):
        if role == "system" and content.startswith("Conversation Summary:"):
            last_summary = content.replace("Conversation Summary: ", "")
            last_summary_index = i
            break
    
    # Return messages after the last summary and the summary itself
    unsummarized = history[last_summary_index + 1:] if last_summary_index != -1 else history
    return unsummarized, last_summary

def summarize_conversation(session_id: str) -> str:
    """Generate a summary of the conversation by combining last summary with new messages."""
    # Get unsummarized messages and last summary
    unsummarized_messages, last_summary = get_unsummarized_messages(session_id)
    
    # Build the conversation text for summarization with clear sections
    conversation_text = ""
    if last_summary:
        conversation_text += f"{SUMMARY_SECTION_HEADER}\n"
        conversation_text += f"{last_summary}\n\n"
    
    conversation_text += f"{NEW_MESSAGES_SECTION_HEADER}\n"
    conversation_text += "\n".join([f"{role}: {content}" for role, content in unsummarized_messages])
    
    # Get new summary from LLM
    summary_prompt = get_summary_prompt(conversation_text)
    summary = call_bedrock_model(summary_prompt)
    
    # Save new summary as a system message
    save_message(session_id, "system", f"Conversation Summary: {summary}")
    
    logger.info(f"Generated new summary combining previous summary with {len(unsummarized_messages)} new messages")
    return summary

def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in a given text."""
    return len(text) // CHARS_PER_TOKEN

def generate_prompt_with_history(session_id: str, user_prompt: str) -> str:
    """Generate a complete prompt including conversation history and summary."""
    history = get_conversation_history(session_id)
    
    # Start with the current prompt
    current_prompt = f"User: {user_prompt}"
    
    # Initialize prompt with system prompts and current message
    complete_prompt = ""
    
    # Find most recent summary
    summary = None
    summary_index = -1
    for i, (role, content) in enumerate(history):
        if role == "system" and content.startswith("Conversation Summary:"):
            summary = content
            summary_index = i
            break
    
    # If we have a summary, add it
    if summary:
        complete_prompt += f"{summary}\n\n"
        
        # Get unsummarized messages (after summary) within token budget
        if summary_index != -1:
            unsummarized = history[summary_index + 1:]
            token_budget = MAX_UNSUMMARIZED_TOKENS
            
            for role, content in unsummarized:
                message = f"{role}: {content}\n"
                message_tokens = estimate_tokens(message)
                if token_budget >= message_tokens:
                    complete_prompt += message
                    token_budget -= message_tokens
                else:
                    # Log if we're truncating unsummarized history
                    logger.info(f"Truncating unsummarized history due to token budget")
                    break
    else:
        # If no summary, just include recent messages within token budget
        token_budget = MAX_UNSUMMARIZED_TOKENS
        for role, content in reversed(history[-5:]):
            message = f"{role}: {content}\n"
            message_tokens = estimate_tokens(message)
            if token_budget >= message_tokens:
                complete_prompt = message + complete_prompt
                token_budget -= message_tokens
            else:
                break
    
    # Add the current prompt
    complete_prompt += f"\nCurrent message:\n{current_prompt}"
    
    # Log token estimation for unsummarized portion
    unsummarized_tokens = estimate_tokens(complete_prompt) - estimate_tokens(summary if summary else "")
    logger.info(f"Estimated tokens in unsummarized portion: {unsummarized_tokens}")
    
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
            logger.info(f"Created new session: {session_id}")

        # Check if we need to summarize based on token count
        unsummarized_messages, _ = get_unsummarized_messages(session_id)
        unsummarized_text = "\n".join([f"{role}: {content}" for role, content in unsummarized_messages])
        if estimate_tokens(unsummarized_text) >= MAX_UNSUMMARIZED_TOKENS:
            logger.info(f"Summarizing conversation for session {session_id}")
            summarize_conversation(session_id)

        # Generate complete prompt with history
        full_prompt = generate_prompt_with_history(session_id, prompt)
        logger.info(f"Generated prompt with length: {len(full_prompt)}")

        # Get text response from Bedrock
        response_text = call_bedrock_model(full_prompt)
        if not response_text:
            logger.error("No response text received from Bedrock")
            return "", None, "Failed to get response from language model", {}

        # Generate audio if requested
        audio_data = None
        audio_path = None
        if config_params.get("generate_audio"):
            try:
                audio_data, audio_path = call_polly_tts(
                    response_text,
                    session_id,
                    str(uuid.uuid4()),
                    voice_id=config_params.get("voice", "Zhiyu")
                )
                if not audio_data:
                    logger.error("No audio data received from Polly")
            except Exception as e:
                logger.error(f"TTS generation failed: {str(e)}")

        # Save messages to database
        save_message(session_id, "user", prompt)
        save_message(session_id, "assistant", response_text, audio_path)
        
        response_details = {
            "timestamp": time.time(),
            "prompt_length": len(prompt),
            "response_length": len(response_text),
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