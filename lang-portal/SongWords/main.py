import logging
import httpx
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
from dotenv import load_dotenv
from agent import LyricsAgent
from database import Database
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Set the Ollama server address from environment variables
OLLAMA_API_BASE = os.getenv("OLLAMA_API_BASE", "http://localhost:8008")
logger.info(f"Ollama API Base URL: {OLLAMA_API_BASE}")

# Initialize database
db = Database()

app = FastAPI(
    title="Song Vocabulary API", 
    description="An API to get lyrics and extract vocabulary from songs in Putonghua"
)

@app.on_event("startup")
async def startup_event():
    db.create_tables()
    # Run the test connection during startup
    await test_ollama_connection()

class LyricsRequest(BaseModel):
    message_request: str
    artist_name: Optional[str] = None

class VocabularyItem(BaseModel):
    word: str
    jiantizi: str
    pinyin: str
    english: str

class LyricsResponse(BaseModel):
    lyrics: str
    vocabulary: List[Dict[str, Any]]

class TextRequest(BaseModel):
    text: str

@app.get("/")
async def root():
    return {"message": "Welcome to the Song Vocabulary API"}

# LyricsAgent class to interact process requests using the LLM
@app.post("/api/agent")
async def get_lyrics(request: LyricsRequest):
    """Get lyrics and vocabulary for a song."""
    try:
        logger.info(f"Processing request: {request.message_request}")
        agent = LyricsAgent()
        result = await agent.run(request.message_request, request.artist_name)
        
        if not result or "lyrics" not in result:
            logger.error("No lyrics found in result")
            raise HTTPException(status_code=404, detail="No lyrics found")
        
        # Store the result in the database
        db.save_song(
            artist=request.artist_name or "Unknown", 
            title=request.message_request,
            lyrics=result["lyrics"],
            vocabulary=result["vocabulary"]
        )
        
        return result
    except Exception as e:
        logger.error(f"Error in get_lyrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Request to the LLM to analyze the provided text and extract vocabulary items
@app.post("/api/get_vocabulary")
async def get_vocabulary(request: TextRequest):
    try:
        logger.info(f"Processing vocabulary request for text of length: {len(request.text)}")
        agent = LyricsAgent()
        vocabulary = await agent.extract_vocabulary(request.text)
        return {"vocabulary": vocabulary}
    except Exception as e:
        logger.error(f"Error in get_vocabulary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def test_ollama_connection():
    try:
        async with httpx.AsyncClient(base_url="http://localhost:8008") as client:
            logger.info("Testing Ollama connection...")
            async with client.stream(
                "POST",
                "/api/generate",
                json={
                    "model": "phi3:3.8b",
                    "prompt": "Hello"
                }
            ) as response:
                logger.info(f"Response status: {response.status_code}")
                response_content = ""
                async for chunk in response.aiter_text():
                    try:
                        chunk_data = json.loads(chunk)
                        if "response" in chunk_data:
                            response_content += chunk_data["response"]
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse chunk as JSON: {chunk[:50]}...")
                logger.info(f"Complete response: {response_content[:100]}...")
                
    except Exception as e:
        logger.error(f"Error testing Ollama connection: {str(e)}")

# Make sure there is NO asyncio.run(test_ollama_connection()) call here or anywhere else in the file

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)