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
VLLM_API_BASE = os.getenv("VLLM_API_BASE", "http://localhost:8008")

class ExampleService:
    def __init__(self, host="0.0.0.0", port=8000):
        print('Initializing Example Service')
        os.environ["TELEMETRY_ENDPOINT"] = ""
        self.host = host
        self.port = port
        self.endpoint = "/v1/example-service"
        self.megaservice = ServiceOrchestrator()
        self.vllm_client = httpx.AsyncClient(base_url=VLLM_API_BASE)
        logger.info(f"Initialized with VLLM API base: {VLLM_API_BASE}")

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
                "name": "VLLM Chat Service",
                "version": "1.0",
                "endpoints": {
                    "/v1/example-service": {
                        "method": "POST",
                        "description": "Chat completion endpoint",
                        "example_request": {
                            "model": "Qwen/Qwen2.5-0.5B-Instruct",
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
        """Format messages into VLLM-compatible format"""
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

    async def call_vllm(self, model: str, messages: list):
        """Make direct call to VLLM API with chat completions support"""
        try:
            # Format messages for the chat completions API
            formatted_messages = []
            if isinstance(messages, list):
                for msg in messages:
                    if hasattr(msg, 'role') and hasattr(msg, 'content'):
                        formatted_messages.append({
                            "role": msg.role,
                            "content": msg.content
                        })
                    elif isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                        formatted_messages.append(msg)
            
            logger.info(f"Calling VLLM at {self.vllm_client.base_url}/v1/chat/completions")
            logger.info(f"Request payload: {{'model': {model}, 'messages': {formatted_messages}}}")
            
            # Use the chat completions endpoint
            response = await self.vllm_client.post(
                "/v1/chat/completions",
                json={
                    "model": model,
                    "messages": formatted_messages,
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=30.0
            )
            response.raise_for_status()
            response_data = response.json()
            
            logger.info(f"VLLM response: {response_data}")
            
            # Extract the assistant's message from the response
            if 'choices' in response_data and len(response_data['choices']) > 0:
                assistant_message = response_data['choices'][0]['message']['content']
                return {"response": assistant_message}
            else:
                return {"response": "No response generated"}

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
            
            # Call VLLM directly
            vllm_response = await self.call_vllm(
                model=request.model or "Qwen/Qwen2.5-0.5B-Instruct",
                messages=request.messages
            )
            logger.info(f"VLLM response: {vllm_response}")

            # Extract content from VLLM response
            assistant_message = vllm_response.get('response', '')
            
            # Create the response
            response = ChatCompletionResponse(
                model=request.model or "Qwen/Qwen2.5-0.5B-Instruct",
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
            await self.vllm_client.aclose()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

if __name__ == "__main__":
    example = ExampleService()
    example.start()