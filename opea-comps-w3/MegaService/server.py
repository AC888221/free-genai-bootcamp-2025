from fastapi import FastAPI, HTTPException, Request, Response
import httpx
import logging
import os
import uvicorn
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://localhost:8008")
TTS_ENDPOINT = os.getenv("TTS_ENDPOINT", "http://localhost:9088")
MEGASERVICE_PORT = int(os.getenv("MEGASERVICE_PORT", 9500))

# Define models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: bool = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000

class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "default"
    output_format: Optional[str] = "wav"

class MegaServiceRequest(BaseModel):
    text: str
    model: str = "Qwen/Qwen2.5-0.5B-Instruct"
    voice: Optional[str] = "default"
    generate_audio: bool = True
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000

class MegaServiceResponse(BaseModel):
    text_response: str
    audio_data: Optional[str] = None  # Base64 encoded audio
    audio_format: Optional[str] = None

# Create FastAPI app
app = FastAPI(title="OPEA MegaService", 
              description="Combined LLM and TTS service",
              version="1.0.0")

# Create HTTP clients
llm_client = httpx.AsyncClient(base_url=LLM_ENDPOINT)
tts_client = httpx.AsyncClient(base_url=TTS_ENDPOINT)

@app.get("/")
async def root():
    return {
        "name": "OPEA MegaService",
        "version": "1.0.0",
        "description": "Combined LLM and TTS service",
        "endpoints": {
            "/v1/chat/completions": "LLM chat completions endpoint",
            "/v1/tts": "Text-to-Speech endpoint",
            "/v1/megaservice": "Combined LLM and TTS endpoint"
        }
    }

@app.get("/health")
async def health():
    try:
        # Check LLM service
        llm_health = await llm_client.get("/health")
        llm_health.raise_for_status()
        
        # Check TTS service
        tts_health = await tts_client.get("/health")
        tts_health.raise_for_status()
        
        return {"status": "healthy", "llm": "ok", "tts": "ok"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """Proxy endpoint for LLM chat completions"""
    try:
        response = await llm_client.post(
            "/v1/chat/completions",
            json=request.dict()
        )
        response.raise_for_status()
        return Response(content=response.content, media_type="application/json")
    except Exception as e:
        logger.error(f"Error calling LLM service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calling LLM service: {str(e)}")

@app.post("/v1/tts")
async def text_to_speech(request: TTSRequest):
    """Direct endpoint for GPT-SoVITS service"""
    try:
        response = await tts_client.post(
            "/tts",  # GPT-SoVITS endpoint
            json={
                "text": request.text,
                "voice": request.voice,
                "language": "en"  # Add any additional GPT-SoVITS parameters here
            }
        )
        response.raise_for_status()
        return Response(content=response.content, media_type="audio/wav")
    except Exception as e:
        logger.error(f"Error calling GPT-SoVITS service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calling GPT-SoVITS service: {str(e)}")

@app.post("/v1/megaservice", response_model=MegaServiceResponse)
async def megaservice(request: MegaServiceRequest):
    """Combined endpoint that calls both LLM and TTS services"""
    try:
        # Step 1: Call LLM service
        llm_request = ChatCompletionRequest(
            model=request.model,
            messages=[ChatMessage(role="user", content=request.text)],
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        llm_response = await llm_client.post(
            "/v1/chat/completions",
            json=llm_request.dict()
        )
        llm_response.raise_for_status()
        llm_data = llm_response.json()
        
        # Extract text response
        text_response = llm_data["choices"][0]["message"]["content"]
        
        # Initialize response
        response = MegaServiceResponse(text_response=text_response)
        
        # Step 2: Call TTS service if requested
        if request.generate_audio:
            tts_response = await tts_client.post(
                "/tts",
                json={"text": text_response, "voice": request.voice}
            )
            tts_response.raise_for_status()
            
            # Convert audio data to base64
            audio_data = base64.b64encode(tts_response.content).decode("utf-8")
            response.audio_data = audio_data
            response.audio_format = "wav"
        
        return response
    
    except Exception as e:
        logger.error(f"Error in megaservice: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in megaservice: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    await llm_client.aclose()
    await tts_client.aclose()

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=MEGASERVICE_PORT, log_level="info") 