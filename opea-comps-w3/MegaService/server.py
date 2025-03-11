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
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://vllm-openvino-arc:8008")
TTS_ENDPOINT = os.getenv("TTS_ENDPOINT", "http://gptsovits-service:9880")
MEGASERVICE_PORT = int(os.getenv("MEGASERVICE_PORT", 9500))
TTS_DEFAULT_REF_WAV = os.getenv("TTS_DEFAULT_REF_WAV", "welcome_cn.wav")
TTS_DEFAULT_PROMPT = os.getenv("TTS_DEFAULT_PROMPT", "欢迎使用")
TTS_DEFAULT_LANGUAGE = os.getenv("TTS_DEFAULT_LANGUAGE", "zh")

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
    base_url=os.getenv("TTS_ENDPOINT", "http://gptsovits-service:9880"),
    timeout=30.0
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
            "/v1/megaservice": "Combined LLM and TTS endpoint"
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
        # Check TTS service health using the endpoint we know works
        async with httpx.AsyncClient() as client:
            tts_endpoint = os.getenv('TTS_ENDPOINT', 'http://tts-gptsovits-service:9088')
            # Use the v1/audio/speech endpoint that we know works
            tts_response = await client.get(f"{tts_endpoint}/v1/audio/speech")
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
            llm_endpoint = os.getenv("LLM_ENDPOINT", "http://vllm-openvino-arc:8008")
            llm_response = await client.get(f"{llm_endpoint}/health")
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

async def try_tts_endpoints(client: httpx.AsyncClient, text: str) -> tuple[bool, Optional[bytes], Optional[str], Optional[str]]:
    """Try all TTS endpoints in sequence with detailed logging"""
    all_errors = []
    
    for endpoint in TTS_ENDPOINTS:
        tts_logger.info(f"Trying endpoint: {endpoint}")
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
                tts_logger.info(f"Trying endpoint {endpoint} with payload format {i+1}: {json.dumps(payload, indent=2)}")
                
                # Log request details
                http_logger.info(f"TTS Request to {endpoint} with payload format {i+1}:")
                http_logger.info(f"URL: {full_url}")
                http_logger.info(f"Headers: {dict(client.headers)}")
                http_logger.info(f"Payload: {json.dumps(payload, indent=2)}")
                
                response = await client.post(
                    endpoint,
                    json=payload,
                    timeout=30.0
                )
                
                # Log response details
                http_logger.info(f"TTS Response from {endpoint} with payload format {i+1}:")
                http_logger.info(f"Status: {response.status_code}")
                http_logger.info(f"Headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    content = response.content
                    content_size = len(content)
                    tts_logger.info(f"Success with endpoint {endpoint}, content size: {content_size} bytes")
                    
                    if content_size > 100:  # Basic size validation
                        return True, content, None, endpoint
                    else:
                        tts_logger.warning(f"Response from {endpoint} too small: {content_size} bytes")
                else:
                    try:
                        error_content = response.content.decode('utf-8')[:500]
                        tts_logger.warning(f"Failed with status {response.status_code} for endpoint {endpoint}")
                        tts_logger.warning(f"Error response: {error_content}")
                        http_logger.error(f"Error content from {endpoint}: {error_content}")
                        all_errors.append(f"Endpoint {endpoint} with payload {i+1}: Status {response.status_code} - {error_content[:100]}...")
                    except Exception as decode_error:
                        tts_logger.warning(f"Could not decode error response from {endpoint}: {str(decode_error)}")
                        all_errors.append(f"Endpoint {endpoint} with payload {i+1}: Decode error - {str(decode_error)}")
                        
            except Exception as e:
                tts_logger.exception(f"Exception with endpoint {endpoint}, payload format {i+1}: {str(e)}")
                all_errors.append(f"Endpoint {endpoint} with payload {i+1}: Exception - {str(e)}")
                continue
    
    # If we get here, all endpoints failed
    error_summary = "\n".join(all_errors)
    tts_logger.error(f"All TTS endpoints failed:\n{error_summary}")
    return False, None, error_summary, None

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
            "text_language": os.getenv("TTS_DEFAULT_LANGUAGE", "zh"),
            "prompt_text": os.getenv("TTS_DEFAULT_PROMPT", "欢迎使用"),
            "prompt_language": os.getenv("TTS_DEFAULT_LANGUAGE", "zh"),
            "refer_wav_path": os.getenv("TTS_DEFAULT_REF_WAV", "welcome_cn.wav")
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

async def generate_tts_audio(text_response: str, custom_params: dict = None):
    """Generate audio from text using TTS service and save to file"""
    tts_logger.info("generate_tts_audio function called")
    
    # Generate a unique filename based on timestamp
    timestamp = int(time.time())
    audio_filename = f"speech_{timestamp}.mp3"
    audio_path = AUDIO_DIR / audio_filename
    
    # Default parameters matching the working curl command
    params = {
        "input": text_response,
        "model": "microsoft/speecht5_tts",
        "voice": "default",
        "response_format": "mp3",
        "speed": 1.0
    }

    if custom_params:
        params.update(custom_params)

    try:
        tts_endpoint = os.getenv('TTS_ENDPOINT', 'http://tts-gptsovits-service:9088')
        url = f"{tts_endpoint}/v1/audio/speech"

        main_logger.info(f"TTS Request URL: {url}")
        main_logger.debug(f"TTS Request Payload: {params}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=params,
                timeout=30.0
            )
            response.raise_for_status()
            
            # Save the audio file
            audio_path.write_bytes(response.content)
            
            # Return the relative path to the audio file
            return str(audio_path.relative_to(Path("static")))

    except httpx.HTTPError as e:
        error_msg = f"TTS request failed: {str(e)}"
        main_logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        error_msg = f"Unexpected error in TTS generation: {str(e)}"
        main_logger.exception(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/v1/megaservice", response_model=MegaServiceResponse)
async def megaservice(request: MegaServiceRequest):
    """Combined LLM and TTS endpoint with comprehensive logging"""
    try:
        request_id = f"req_{int(time.time())}_{id(request)}"
        main_logger.info(f"[{request_id}] Received megaservice request")
        main_logger.info(f"[{request_id}] Request: {request.dict()}")
        
        # Get LLM response first
        llm_request = ChatCompletionRequest(
            model=request.model,
            messages=[ChatMessage(role="user", content=request.text)],
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        llm_logger.info(f"[{request_id}] Sending LLM request")
        llm_logger.debug(f"[{request_id}] Request payload: {llm_request.dict()}")
        
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
            
            try:
                audio_content = await generate_tts_audio(text_response)
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

@app.on_event("shutdown")
async def shutdown_event():
    await llm_client.aclose()
    await tts_client.aclose()

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=MEGASERVICE_PORT, log_level="info") 