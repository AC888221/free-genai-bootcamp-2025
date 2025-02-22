from fastapi import FastAPI, HTTPException
import httpx
import logging
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    UsageInfo
)
from comps.cores.mega.constants import ServiceType, ServiceRoleType
from comps import MicroService, ServiceOrchestrator
from dotenv import load_dotenv
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Get environment variables
EMBEDDING_SERVICE_HOST_IP = os.getenv("EMBEDDING_SERVICE_HOST_IP", "0.0.0.0")
EMBEDDING_SERVICE_PORT = os.getenv("EMBEDDING_SERVICE_PORT", 6000)
LLM_SERVICE_HOST_IP = os.getenv("LLM_SERVICE_HOST_IP", "0.0.0.0")
LLM_SERVICE_PORT = os.getenv("LLM_SERVICE_PORT", 9000)
OLLAMA_API_BASE = os.getenv("OLLAMA_API_BASE", "http://localhost:8008")

class ExampleService:
    def __init__(self, host="0.0.0.0", port=8000):
        print('Initializing Example Service')
        os.environ["TELEMETRY_ENDPOINT"] = ""
        self.host = host
        self.port = port
        self.endpoint = "/v1/example-service"
        self.megaservice = ServiceOrchestrator()
        self.ollama_client = httpx.AsyncClient(base_url=OLLAMA_API_BASE)
        logger.info(f"Initialized with Ollama API base: {OLLAMA_API_BASE}")

    def start(self):
        self.service = MicroService(
            self.__class__.__name__,
            service_role=ServiceRoleType.MEGASERVICE,
            host=self.host,
            port=self.port,
            endpoint=self.endpoint,
            input_datatype=ChatCompletionRequest,
            output_datatype=ChatCompletionResponse,
        )

        # Add root route for documentation
        async def root():
            return {
                "name": "Ollama Chat Service",
                "version": "1.0",
                "endpoints": {
                    "/v1/example-service": {
                        "method": "POST",
                        "description": "Chat completion endpoint",
                        "example_request": {
                            "model": "llama3.2:1b",
                            "messages": "What is the capital of France?"
                        }
                    }
                }
            }

        self.service.add_route("/", root, methods=["GET"])
        self.service.add_route(self.endpoint, self.handle_request, methods=["POST"])
        logger.info(f"Added routes: / and {self.endpoint}")
        self.service.start()

    async def format_messages(self, messages):
        """Format messages into Ollama-compatible format"""
        try:
            if isinstance(messages, str):
                return messages
            elif isinstance(messages, list):
                return " ".join([
                    msg.content if hasattr(msg, 'content') else str(msg)
                    for msg in messages
                ])
            return str(messages)
        except Exception as e:
            logger.error(f"Error formatting messages: {str(e)}")
            raise

    async def call_ollama(self, model: str, messages: list):
        """Make direct call to Ollama API with streaming support"""
        try:
            prompt = await self.format_messages(messages)
            logger.info(f"Calling Ollama at {self.ollama_client.base_url}/api/generate")
            logger.info(f"Request payload: {{'model': {model}, 'prompt': {prompt}}}")
            
            async with self.ollama_client.stream(
                "POST",
                "/api/generate",
                json={
                    "model": "llama3.2:1b",
                    "prompt": prompt,
                    "stream": True
                },
                timeout=30.0
            ) as response:
                response.raise_for_status()
                
                # Collect all response chunks
                full_response = ""
                async for chunk in response.aiter_lines():
                    if not chunk:
                        continue
                    try:
                        chunk_data = json.loads(chunk)
                        if chunk_data.get("done", False):
                            break
                        full_response += chunk_data.get("response", "")
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding chunk: {e}")
                        continue
                
                logger.info(f"Full response: {full_response}")
                return {"response": full_response}

        except httpx.HTTPError as http_err:
            error_detail = f"HTTP error occurred: {str(http_err)}"
            if hasattr(http_err, 'response'):
                error_detail += f"\nResponse: {http_err.response.text}"
            logger.error(error_detail)
            raise HTTPException(status_code=500, detail=error_detail)
        except Exception as e:
            error_detail = f"Unexpected error: {str(e)}"
            logger.error(error_detail)
            raise HTTPException(status_code=500, detail=error_detail)

    async def handle_request(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        try:
            logger.info(f"Received request: {request}")
            
            # Call Ollama directly
            ollama_response = await self.call_ollama(
                model=request.model or "llama3.2:1b",
                messages=request.messages
            )
            logger.info(f"Ollama response: {ollama_response}")

            # Extract content from Ollama response
            assistant_message = ollama_response.get('response', '')
            
            # Create the response
            response = ChatCompletionResponse(
                model=request.model or "llama3.2:1b",
                choices=[
                    ChatCompletionResponseChoice(
                        index=0,
                        message=ChatMessage(
                            role="assistant",
                            content=assistant_message
                        ),
                        finish_reason="stop"
                    )
                ],
                usage=UsageInfo(
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0
                )
            )
            
            return response

        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self.ollama_client.aclose()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

if __name__ == "__main__":
    example = ExampleService()
    example.start()