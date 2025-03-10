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
TTS_DEFAULT_REF_WAV = os.getenv("TTS_DEFAULT_REF_WAV", "welcome_cn.wav")
TTS_DEFAULT_PROMPT = os.getenv("TTS_DEFAULT_PROMPT", "欢迎使用")
TTS_DEFAULT_LANGUAGE = os.getenv("TTS_DEFAULT_LANGUAGE", "zh")

# Add known TTS endpoints and make them visible in logs
TTS_ENDPOINTS = ["/", "/generate", "/tts", "/v1/audio/speech"]
logger.info(f"Configured TTS endpoints: {TTS_ENDPOINTS}")

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
    error_message: Optional[str] = None

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
    """Health check that verifies basic service functionality without requiring vLLM."""
    try:
        # Basic service health check
        return {"status": "healthy", "service": "megaservice"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Service unhealthy")

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

async def try_tts_request(client: httpx.AsyncClient, endpoint: str, payload: dict) -> tuple[bool, Optional[bytes], Optional[str]]:
    """
    Try a TTS request with detailed logging and error handling.
    Returns: (success, audio_content, error_message)
    """
    full_url = f"{client.base_url.rstrip('/')}{endpoint}"
    try:
        logger.info(f"Attempting TTS request to: {full_url}")
        logger.info(f"TTS request payload: {json.dumps(payload)}")
        
        response = await client.post(
            endpoint,
            json=payload,
            timeout=30.0
        )
        
        logger.info(f"TTS response status [{endpoint}]: {response.status_code}")
        logger.info(f"TTS response headers [{endpoint}]: {dict(response.headers)}")
        
        if response.status_code == 404:
            return False, None, f"Endpoint not found: {full_url}"
            
        response.raise_for_status()
        
        if not response.content:
            return False, None, f"Empty response from TTS service at {endpoint}"
            
        logger.info(f"Successfully received {len(response.content)} bytes from {endpoint}")
        return True, response.content, None
        
    except httpx.TimeoutException:
        logger.warning(f"Timeout calling {full_url}")
        return False, None, f"Timeout calling {endpoint}"
    except httpx.RequestError as e:
        logger.warning(f"Request error for {full_url}: {str(e)}")
        return False, None, f"Request error: {str(e)}"
    except Exception as e:
        error_msg = f"TTS error at {endpoint}: {str(e)}"
        if hasattr(e, 'response'):
            error_msg += f"\nResponse: {e.response.text if e.response else 'No response'}"
        logger.error(error_msg)
        return False, None, error_msg

async def make_tts_request(client: httpx.AsyncClient, text: str) -> tuple[bool, Optional[bytes], Optional[str]]:
    """
    Try multiple TTS endpoints with fallback and logging.
    Returns: (success, audio_content, error_message)
    """
    payload = {
        "text": text,
        "text_language": TTS_DEFAULT_LANGUAGE,
        "prompt_text": TTS_DEFAULT_PROMPT,
        "prompt_language": TTS_DEFAULT_LANGUAGE,
        "speed": 1.0,
        "temperature": 1.0,
        "top_k": 15,
        "top_p": 1.0
    }
    
    errors = []
    logger.info(f"Starting TTS request attempts for text: {text[:100]}...")
    
    # Try each endpoint in order
    for endpoint in TTS_ENDPOINTS:
        logger.info(f"Trying TTS endpoint: {endpoint}")
        success, content, error = await try_tts_request(client, endpoint, payload)
        if success:
            logger.info(f"Successfully generated audio using endpoint: {endpoint}")
            return True, content, None
        errors.append(f"Endpoint {endpoint}: {error}")
        logger.warning(f"Failed attempt with {endpoint}: {error}")
    
    # If we get here, all endpoints failed
    error_msg = "All TTS endpoints failed:\n" + "\n".join(errors)
    logger.error(error_msg)
    return False, None, error_msg

@app.post("/v1/tts")
async def text_to_speech(request: TTSRequest):
    """Direct endpoint for GPT-SoVITS service"""
    success, content, error = await make_tts_request(tts_client, request.text)
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Error calling GPT-SoVITS service: {error}")
    
    return Response(content=content, media_type="audio/wav")

@app.post("/v1/megaservice", response_model=MegaServiceResponse)
async def megaservice(request: MegaServiceRequest):
    try:
        # Try to call LLM service
        try:
            llm_request = ChatCompletionRequest(
                model=request.model,
                messages=[ChatMessage(role="user", content=request.text)],
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            logger.info(f"Sending LLM request: {llm_request.dict()}")
            llm_response = await llm_client.post(
                "/v1/chat/completions",
                json=llm_request.dict()
            )
            llm_response.raise_for_status()
            llm_data = llm_response.json()
            text_response = llm_data["choices"][0]["message"]["content"]
            logger.info(f"Received LLM response: {text_response[:100]}...")
        except Exception as llm_error:
            logger.exception("LLM service error")
            raise HTTPException(status_code=500, detail=f"LLM service error: {str(llm_error)}")

        # Initialize response
        response = MegaServiceResponse(text_response=text_response)
        
        # Try TTS service if requested
        if request.generate_audio:
            logger.info("Starting TTS generation attempt")
            success, audio_content, error = await make_tts_request(tts_client, text_response)
            
            if success:
                logger.info("Successfully generated audio")
                response.audio_data = base64.b64encode(audio_content).decode("utf-8")
                response.audio_format = "wav"
            else:
                logger.error(f"Failed to generate audio: {error}")
                # Don't raise an exception, just continue without audio
                response.error_message = f"Audio generation failed: {error}"
        
        return response
    except Exception as e:
        logger.exception("Error in megaservice")
        raise HTTPException(status_code=500, detail=f"Error in megaservice: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    await llm_client.aclose()
    await tts_client.aclose()

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=MEGASERVICE_PORT, log_level="info") 