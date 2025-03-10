from fastapi import FastAPI, HTTPException, Request, Response
import httpx
import logging
import os
import uvicorn
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import base64
import logging.handlers

# Configure logging
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Setup different loggers for different components
def setup_logger(name, log_file, level=logging.INFO):
    """Function to setup as many loggers as needed"""
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    fh = logging.handlers.RotatingFileHandler(
        os.path.join(LOG_DIR, log_file),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    fh.setFormatter(formatter)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

# Setup individual loggers
main_logger = setup_logger('megaservice', 'megaservice.log')
llm_logger = setup_logger('llm', 'llm.log')
tts_logger = setup_logger('tts', 'tts.log')
http_logger = setup_logger('http', 'http.log')

# Get environment variables
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://localhost:8008")
TTS_ENDPOINT = os.getenv("TTS_ENDPOINT", "http://localhost:9088")
MEGASERVICE_PORT = int(os.getenv("MEGASERVICE_PORT", 9500))
TTS_DEFAULT_REF_WAV = os.getenv("TTS_DEFAULT_REF_WAV", "welcome_cn.wav")
TTS_DEFAULT_PROMPT = os.getenv("TTS_DEFAULT_PROMPT", "欢迎使用")
TTS_DEFAULT_LANGUAGE = os.getenv("TTS_DEFAULT_LANGUAGE", "zh")

# Update TTS endpoints with more variations
TTS_ENDPOINTS = [
    "/api/v1/tts",
    "/v1/tts",
    "/tts/generate",
    "/generate",
    "/tts",
    "/inference",
    "/synthesize",
    "/api/synthesize",
    "/api/inference"
]

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
        main_logger.error(f"Health check failed: {str(e)}")
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
        main_logger.error(f"Error calling LLM service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calling LLM service: {str(e)}")

async def try_tts_request(client: httpx.AsyncClient, endpoint: str, text: str) -> tuple[bool, Optional[bytes], Optional[str]]:
    """Try a TTS request with detailed logging"""
    try:
        tts_logger.info(f"Attempting request to endpoint: {endpoint}")
        full_url = f"{client.base_url.rstrip('/')}{endpoint}"
        tts_logger.info(f"Full URL: {full_url}")
        
        # Different payload formats to try
        payloads = [
            {
                "text": text,
                "text_language": TTS_DEFAULT_LANGUAGE,
                "prompt_text": TTS_DEFAULT_PROMPT,
                "prompt_language": TTS_DEFAULT_LANGUAGE,
            },
            {
                "input": text,
                "language": TTS_DEFAULT_LANGUAGE,
            },
            {
                "text": text,
                "language": TTS_DEFAULT_LANGUAGE,
            }
        ]
        
        for i, payload in enumerate(payloads):
            try:
                tts_logger.info(f"Trying payload format {i+1}: {json.dumps(payload, indent=2)}")
                
                # Log request details
                http_logger.info(f"TTS Request {i+1}:")
                http_logger.info(f"URL: {full_url}")
                http_logger.info(f"Headers: {dict(client.headers)}")
                http_logger.info(f"Payload: {json.dumps(payload, indent=2)}")
                
                response = await client.post(
                    endpoint,
                    json=payload,
                    timeout=30.0
                )
                
                # Log response details
                http_logger.info(f"TTS Response {i+1}:")
                http_logger.info(f"Status: {response.status_code}")
                http_logger.info(f"Headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    content = response.content
                    content_size = len(content)
                    tts_logger.info(f"Success with endpoint {endpoint}, content size: {content_size} bytes")
                    
                    if content_size > 100:  # Basic size validation
                        return True, content, None
                    else:
                        tts_logger.warning(f"Response too small: {content_size} bytes")
                else:
                    try:
                        error_content = response.content.decode('utf-8')[:500]
                        tts_logger.warning(f"Failed with status {response.status_code}")
                        tts_logger.warning(f"Error response: {error_content}")
                        http_logger.error(f"Error content: {error_content}")
                    except Exception as decode_error:
                        tts_logger.warning(f"Could not decode error response: {str(decode_error)}")
                        
            except Exception as e:
                tts_logger.exception(f"Error with payload format {i+1}")
                continue
                
        return False, None, f"All payload formats failed for endpoint {endpoint}"
        
    except Exception as e:
        tts_logger.exception(f"Request failed for {endpoint}")
        return False, None, str(e)

@app.post("/v1/tts")
async def text_to_speech(request: TTSRequest):
    """Direct endpoint for GPT-SoVITS service"""
    success, content, error = await try_tts_request(tts_client, request.text, request.text)
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Error calling GPT-SoVITS service: {error}")
    
    return Response(content=content, media_type="audio/wav")

@app.get("/debug/tts-info")
async def tts_info():
    """Debug endpoint to check TTS service configuration"""
    try:
        # Try to get TTS service info
        response = await tts_client.get("/")
        service_info = {
            "base_url": str(tts_client.base_url),
            "status": "available",
            "root_response": response.status_code,
            "headers": dict(response.headers)
        }
        
        # Try each endpoint
        endpoint_status = {}
        for endpoint in TTS_ENDPOINTS:
            try:
                response = await tts_client.get(endpoint)
                endpoint_status[endpoint] = {
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type", "unknown")
                }
            except Exception as e:
                endpoint_status[endpoint] = {"error": str(e)}
        
        service_info["endpoints"] = endpoint_status
        return service_info
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "base_url": str(tts_client.base_url)
        }

@app.post("/v1/megaservice", response_model=MegaServiceResponse)
async def megaservice(request: MegaServiceRequest):
    """Combined LLM and TTS endpoint with comprehensive logging"""
    try:
        main_logger.info("Received megaservice request")
        main_logger.info(f"Request: {request.dict()}")
        
        # Get LLM response first
        llm_request = ChatCompletionRequest(
            model=request.model,
            messages=[ChatMessage(role="user", content=request.text)],
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        llm_logger.info("Sending LLM request")
        llm_logger.debug(f"Request payload: {llm_request.dict()}")
        
        llm_response = await llm_client.post(
            "/v1/chat/completions",
            json=llm_request.dict()
        )
        llm_response.raise_for_status()
        
        llm_data = llm_response.json()
        text_response = llm_data["choices"][0]["message"]["content"]
        llm_logger.info(f"Got LLM response: {text_response[:100]}...")
        
        # Initialize response
        response = MegaServiceResponse(text_response=text_response)
        
        # Try TTS if requested
        if request.generate_audio:
            main_logger.info("Starting TTS generation")
            errors = []
            
            for endpoint in TTS_ENDPOINTS:
                tts_logger.info(f"Trying endpoint: {endpoint}")
                success, content, error = await try_tts_request(tts_client, endpoint, text_response)
                
                if success:
                    main_logger.info(f"TTS generation successful with endpoint {endpoint}")
                    response.audio_data = base64.b64encode(content).decode("utf-8")
                    response.audio_format = "wav"
                    break
                else:
                    error_msg = f"{endpoint}: {error}"
                    tts_logger.error(error_msg)
                    errors.append(error_msg)
            
            if not response.audio_data:
                error_msg = "Failed to generate audio with any endpoint:\n" + "\n".join(errors)
                main_logger.error(error_msg)
                response.error_message = error_msg
        
        main_logger.info("Request completed successfully")
        return response
        
    except Exception as e:
        main_logger.exception("Service error")
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    await llm_client.aclose()
    await tts_client.aclose()

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=MEGASERVICE_PORT, log_level="info") 