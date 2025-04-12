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
import time
from pathlib import Path

# Define the directory for storing audio files
AUDIO_DIR = Path("audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

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
main_logger = setup_logger('megaservice', 'megaservice.log', level=logging.DEBUG)
llm_logger = setup_logger('llm', 'llm.log')
tts_logger = setup_logger('tts', 'tts.log')
http_logger = setup_logger('http', 'http.log')

# Get environment variables
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://localhost:8008")
TTS_ENDPOINT = os.getenv("TTS_ENDPOINT", "http://localhost:9880")
MEGASERVICE_PORT = int(os.getenv("MEGASERVICE_PORT", 9500))
TTS_DEFAULT_REF_WAV = os.getenv("TTS_DEFAULT_REF_WAV", "welcome_cn.wav")
TTS_DEFAULT_PROMPT = os.getenv("TTS_DEFAULT_PROMPT", "欢迎使用")
TTS_DEFAULT_LANGUAGE = os.getenv("TTS_DEFAULT_LANGUAGE", "zh")

# Instead of importing GPT_SOVITS_URL from config.py
# Use the environment variable directly
GPT_SOVITS_URL = os.getenv('TTS_ENDPOINT', f"http://localhost:{os.getenv('GPT_SOVITS_PORT', '9880')}")

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
    text_language: str = Field(default="zh")
    prompt_text: str = Field(default="欢迎使用")
    prompt_language: str = Field(default="zh")
    refer_wav_path: str = Field(default="welcome_cn.wav")

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
tts_client = httpx.AsyncClient(
    base_url=TTS_ENDPOINT,
    timeout=60.0
)

@app.get("/")
async def root():
    return {
        "name": "OPEA MegaService",
        "version": "1.0.0",
        "description": "Combined LLM and TTS service",
        "endpoints": {
            "/v1/chat/completions": "LLM chat completions endpoint",
            "/v1/tts": "Text-to-Speech endpoint",
            "/v1/megaservice": "Combined LLM and TTS endpoint",
            "/v1/audio/files": "List available audio files",
            "/audio/{filename}": "Serve audio files"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    status = {
        "llm_service": "unknown",
        "tts_service": "unknown",
        "megaservice": "online"
    }
    
    try:
        # Check TTS service health
        async with httpx.AsyncClient() as client:
            tts_response = await client.get(f"{TTS_ENDPOINT}/")
            if tts_response.status_code in [200, 404]:  # 404 is okay for GET on POST endpoint
                status["tts_service"] = "online"
            else:
                status["tts_service"] = "error"
                main_logger.error(f"TTS health check failed with status {tts_response.status_code}")
    except Exception as e:
        status["tts_service"] = "error"
        main_logger.error(f"TTS health check failed: {str(e)}")

    try:
        # Check LLM service health
        async with httpx.AsyncClient() as client:
            llm_response = await client.get(f"{LLM_ENDPOINT}/health")
            if llm_response.status_code == 200:
                status["llm_service"] = "online"
            else:
                status["llm_service"] = "error"
                main_logger.error(f"LLM health check failed with status {llm_response.status_code}")
    except Exception as e:
        status["llm_service"] = "error"
        main_logger.error(f"LLM health check failed: {str(e)}")

    return status

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    http_logger.info("chat_completions endpoint called")
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

async def generate_tts_audio(text_response: str, custom_params: dict = None):
    """
    Generate audio from text using TTS service, save to file and return the content
    
    Args:
        text_response: The text to convert to speech
        custom_params: Optional dictionary of parameters to customize the TTS request
        
    Returns:
        bytes: The audio content as bytes
    """
    tts_logger.info(f"Generating TTS for text: {text_response[:50]}...")
    
    # Generate a unique filename based on timestamp
    timestamp = int(time.time())
    audio_filename = f"speech_{timestamp}.wav"
    audio_path = AUDIO_DIR / audio_filename
    
    # Base parameters for GPT-SoVITS
    params = {
        "input": text_response,  # Make sure this matches what GPT-SoVITS expects
        # Other parameters as needed
    }
    
    # Update with any custom parameters
    if custom_params:
        params.update(custom_params)
    
    try:
        # Log request details
        tts_logger.info(f"TTS Request to {TTS_ENDPOINT}/v1/audio/speech")
        tts_logger.debug(f"TTS Params: {json.dumps(params, indent=2)}")
        
        # Make the request to the TTS endpoint
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{TTS_ENDPOINT}/v1/audio/speech",  # Use the correct endpoint
                json=params
            )
            response.raise_for_status()
            
            # Get the audio content
            audio_content = response.content
            
            # Validate content
            if len(audio_content) < 100:
                raise ValueError(f"TTS response too small: {len(audio_content)} bytes")
                
            # Save the audio file
            audio_path.write_bytes(audio_content)
            tts_logger.info(f"Saved audio to {audio_path}")
            
            # Return the audio content
            return audio_content
            
    except Exception as e:
        error_msg = f"TTS generation failed: {str(e)}"
        tts_logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/v1/tts")
async def text_to_speech(request: TTSRequest):
    """Direct endpoint for GPT-SoVITS service"""
    try:
        # Convert TTSRequest to the format expected by generate_tts_audio
        params = {
            "text": request.text,
            "text_language": request.text_language,
            "prompt_text": request.prompt_text,
            "prompt_language": request.prompt_language,
            "refer_wav_path": request.refer_wav_path
        }
        audio_content = await generate_tts_audio(request.text, params)
        return Response(content=audio_content, media_type="audio/wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling GPT-SoVITS service: {str(e)}")

@app.get("/debug/tts-info")
async def tts_info():
    """Debug endpoint to check TTS service configuration"""
    try:
        # Try to get TTS service info
        response = await tts_client.get("/health")
        service_info = {
            "base_url": str(tts_client.base_url),
            "status": "available" if response.status_code == 200 else "error",
            "health_check": response.status_code
        }
        
        # Try test TTS request
        test_params = {
            "text": "Test",
            "text_language": TTS_DEFAULT_LANGUAGE,
            "prompt_text": TTS_DEFAULT_PROMPT,
            "prompt_language": TTS_DEFAULT_LANGUAGE,
            "refer_wav_path": TTS_DEFAULT_REF_WAV
        }
        
        try:
            test_response = await tts_client.post("/", json=test_params)
            service_info["test_request"] = {
                "status_code": test_response.status_code,
                "content_length": len(test_response.content) if test_response.status_code == 200 else None
            }
        except Exception as e:
            service_info["test_request"] = {"error": str(e)}
        
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
        request_id = f"req_{int(time.time())}"
        main_logger.info(f"[{request_id}] Received megaservice request")
        
        # Get LLM response first
        llm_request = ChatCompletionRequest(
            model=request.model,
            messages=[ChatMessage(role="user", content=request.text)],
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        llm_logger.info(f"[{request_id}] Sending LLM request")
        
        try:
            llm_response = await llm_client.post(
                "/v1/chat/completions",
                json=llm_request.dict(),
                timeout=60.0
            )
            llm_response.raise_for_status()
            
            llm_data = llm_response.json()
            text_response = llm_data["choices"][0]["message"]["content"]
            llm_logger.info(f"[{request_id}] Got LLM response: {text_response[:100]}...")
            
        except Exception as e:
            error_msg = f"LLM service error: {str(e)}"
            llm_logger.exception(f"[{request_id}] {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Initialize response
        response = MegaServiceResponse(text_response=text_response)
        
        # Try TTS if requested
        if request.generate_audio:
            main_logger.info(f"[{request_id}] Starting TTS generation")
            
            # Prepare TTS parameters
            tts_params = {
                "text_language": TTS_DEFAULT_LANGUAGE,
                "prompt_text": TTS_DEFAULT_PROMPT,
                "prompt_language": TTS_DEFAULT_LANGUAGE
            }
            
            # Use custom voice if specified
            if request.voice and request.voice != "default":
                tts_params["refer_wav_path"] = f"{request.voice}.wav"
            
            try:
                audio_content = await generate_tts_audio(text_response, tts_params)
                response.audio_data = base64.b64encode(audio_content).decode("utf-8")
                response.audio_format = "wav"
            except Exception as e:
                main_logger.error(f"TTS generation failed: {str(e)}")
                response.error_message = f"TTS generation failed: {str(e)}"
        
        main_logger.info(f"[{request_id}] Request completed successfully")
        return response
        
    except HTTPException:
        # Re-raise existing HTTP exceptions
        raise
    except Exception as e:
        error_msg = f"Service error: {str(e)}"
        main_logger.exception(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/v1/audio/files")
async def list_audio_files():
    """List all available audio files"""
    try:
        # Get all audio files
        audio_files = list(AUDIO_DIR.glob("*.wav"))
        audio_files.extend(AUDIO_DIR.glob("*.mp3"))
        
        # Sort by creation time (newest first)
        audio_files.sort(key=lambda x: os.path.getctime(x), reverse=True)
        
        # Format response
        files = []
        for file in audio_files:
            file_stats = file.stat()
            files.append({
                "filename": file.name,
                "path": f"/audio/{file.name}",
                "size": file_stats.st_size,
                "created": os.path.getctime(file)
            })
        
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing audio files: {str(e)}")

@app.get("/audio/{filename}")
async def get_audio_file(filename: str):
    """Serve an audio file from the audio directory"""
    file_path = AUDIO_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File {filename} not found")
    
    # Determine content type
    content_type = "audio/wav"
    if filename.lower().endswith(".mp3"):
        content_type = "audio/mpeg"
    
    return Response(content=file_path.read_bytes(), media_type=content_type)

@app.on_event("shutdown")
async def shutdown_event():
    await llm_client.aclose()
    await tts_client.aclose()

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=MEGASERVICE_PORT, log_level="info")