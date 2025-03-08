from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
from agent import LyricsAgent
from database import Database

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
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/get_vocabulary")
async def get_vocabulary(request: TextRequest):
    try:
        agent = LyricsAgent()
        vocabulary = agent.extract_vocabulary(request.text)
        return {"vocabulary": vocabulary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)