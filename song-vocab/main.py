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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Set the Ollama server address from environment variables
OLLAMA_API_BASE = os.getenv("OLLAMA_API_BASE", "http://localhost:8008")

app = FastAPI(title="Song Vocabulary API", 
              description="An API to get lyrics and extract vocabulary from songs in Putonghua")

# Initialize database
db = Database()

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

@app.on_event("startup")
async def startup_event():
    db.create_tables()

@app.get("/")
async def root():
    return {"message": "Welcome to the Song Vocabulary API"}

# LyricsAgent class to interact process requests using the LLM
@app.post("/api/agent", response_model=LyricsResponse)
async def get_lyrics(request: LyricsRequest):
    try:
        agent = LyricsAgent()
        result = agent.run(request.message_request, request.artist_name)
        
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
        async with httpx.AsyncClient(base_url=OLLAMA_API_BASE) as client:
            response = await client.post(
                "/api/generate",
                json={
                    "model": "Phi-3-mini-4k-instruct",
                    "prompt": f"Extract vocabulary from the following text:\n\n{request.text}",
                    "stream": False
                }
            )
            response.raise_for_status()
            vocabulary = response.json().get("vocabulary", [])
            return {"vocabulary": vocabulary}
    except httpx.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {str(http_err)}")
        raise HTTPException(status_code=500, detail=f"HTTP error: {str(http_err)}")
    except Exception as e:
        logger.error(f"Error in get_vocabulary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)