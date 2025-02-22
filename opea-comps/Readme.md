# Running Ollama Third-Party Service

### Choosing a Model

You can get the model_id that ollama will launch from the [Ollama Library](https://ollama.com/library).

https://ollama.com/library/1lama3.2

eg. https://ollama.com/library/llama3.2

### Getting the Host Ip

#### Linux

Get your IP address
```sh
sudo apt install net-tool
if config
```

Or you can try this

HOST_IP=$(hostname -I | awk '{print $1}') NO_PROXY=localhost LLM_ENDPOINT_PORT=8008 LLM_MODEL_ID="1lama3.2:1b" dockercompose up

## Ollama API

Once the Ollama server is running we can make API calls to the Ollama API.

https://github.com/ollama/ollama/blob/main/docs/api.md


## Download (pull) a model

curl http://localhost:8008/api/pull -d '{
    "model": "llama3.2:1b"
}'

## Generate a Request

curl http://localhost:8008/api/generate -d '{
    "model": "llama3.2:1b",
    "prompt": "Why is the sky blue?"
}'

## Technical Uncertainty

**Q:** Can I run Llama 3.2 1B with Llambda on a t2.micro instance?
**A:** Yes, but running Llama 3.2 1B with Llambda on a t2.micro instance would face similar challenges as with Ollama due to the insufficient memory (1 GiB) compared to the model's requirements (2.3GB of VRAM).

**Q:** Why isn't the Docker command recognized in PowerShell when I loaded it from WSL?
**A:** The Docker command isn't recognized in PowerShell because Docker isn't in my system's PATH or Docker Desktop isn't properly integrated with WSL2. I may need to ensure Docker is installed on Windows and properly configured.

**Q:** If I've installed Docker in my Linux WSL, do I need to install it on Windows too?
**A:** I don't necessarily need to install Docker Desktop on Windows if I'm managing Docker entirely within WSL2. However, using Docker Desktop can simplify the integration and provide a GUI for easier management.

**Q:** Why can't I see containers in the Docker extension in VSCode even after connecting?
**A:** Make sure the Docker daemon is running, check the Docker context, and verify that the Docker extension is up to date. I may also need to explicitly set the Docker path in VSCode settings.

**Q:** What should I check if the Docker extension in VSCode cannot connect?
**A:** Check if Docker is running by executing `docker ps`, restart Docker and VSCode, and ensure the Docker context is correct.

**Q:** What are the prerequisites for setting up OPEA with Ollama?
**A:** Before setting up OPEA with Ollama, make sure I have:
- A valid OpenAI API key.
- Ollama installed on my system. I can install it via Homebrew on macOS or follow the installation instructions for my operating system from the Ollama documentation.
- Basic knowledge of command-line operations.

**Q:** Does bridge mode restrict access to the Ollama API to only other models within the Docker Compose setup?
**A:** No, the host machine will still be able to access the Ollama API.

**Q:** What is the mapping for the ports 8008 and 11434?
**A:** In this setup, 8008 is the port that the host machine will use to access the service, while 11434 is the port used by the service inside the container.

**Q:** How can the different variables in the Docker Compose file be configured?
**A:** The variables in the compose file can be configured using environment variables. This approach allows for easy management and switching of configurations. For example, by updating the `LLM_MODEL_ID` environment variable in the `.env` file, I can change the model being used by the service. After making changes to the `.env` file, restarting the service will apply the new configuration. This method ensures flexibility and ease of maintenance for different deployment scenarios.

**Q:** If I pass the `LLM_MODEL_ID` to the Ollama server, will it automatically download the model on startup?
**A:** It doesn't appear so. The Ollama CLI might be running multiple APIs, so I need to call the `/pull` API before trying to generate text.

**Q:** Will the model be downloaded into the container? Does this mean the model will be deleted when the container stops running?
**A:** Yes, the model will be downloaded into the container, and it will be deleted when the container stops running. To persist the model data, I need to mount a local drive.

**Q:** How can I test if my OPEA setup with Ollama is working correctly?
**A:** I can test my setup by running a simple command in Ollama to generate a response. For example:
```sh
curl -X POST http://localhost:8000/v1/example-service \
    -H "Content-Type: application/json" \
    -d '{
        "model": "llama3.2:1b",
        "messages": "Hello, this is a test message"
    }' \
    -o response.json
```

**Q:** How do I handle errors returned by the OpenAI API in my Ollama setup?
**A:** To handle errors returned by the OpenAI API, I should implement error handling in my code. Check the response status and error messages, and log them for debugging. I can also provide user-friendly messages based on the type of error encountered.

**Q:** For LLM services that support text generation, OPEA documentation suggests they will only work with TGI/vLLM and all I have to do is have it running. Do TGI and vLLM have a standardized API, or is there code to detect which one is running? Do I really have to use a Xeon or Gaudi processor?
**A:** TGI and vLLM do not have a standardized API, but they are designed to be compatible with common frameworks and tools. While it is recommended that these tasks are run on a Xeon or Gaudi processor, my results suggest that it is possible to run them on standard CPUs. The performance will be lower on CPUs compared to GPUs, but it is possible to run them without specialized hardware.

# Port change for Megaservice
HOST_IP=$(hostname -I | awk '{print $1}') NO_PROXY=localhost LLM_ENDPOINT_PORT=9000 LLM_MODEL_ID="1lama3.2:1b" dockercompose up
## Download (pull) a model

curl http://localhost:9000/api/pull -d '{
    "model": "llama3.2:1b"
}'

## Generate a Request

curl http://localhost:9000/api/generate -d '{
    "model": "llama3.2:1b",
    "prompt": "Why is the sky blue?"
}'

OPEA Implementation Report

Installation and Setup:

Successfully deployed Ollama using Docker Compose, configuring it to run on port 8008
Set up a FastAPI service as a middleware layer to handle API requests
Integrated the comps library for standardized protocol definitions
Configured environment variables for flexible deployment settings
Feature Implementation:

Developed a chat completion endpoint /v1/example-service that processes user queries
Implemented streaming response handling from the LLM
Integrated error handling and comprehensive logging for debugging
Successfully loaded and utilized the llama3.2:1b model (1.2B parameters)
System Integration:

Created a seamless integration between FastAPI and Ollama's API
Implemented message formatting and response handling for LLM interactions
Set up proper request/response protocols using the comps library
Established a Docker-based deployment strategy for consistency
Technical Challenges Overcome:

Successfully handled streaming responses from the LLM
Implemented proper error handling for API communication
Managed Docker container deployment and configuration
Integrated complex message formatting and response processing
Architecture Implementation:

Designed a three-tier architecture: Client → FastAPI Service → Ollama (LLM)
Implemented proper separation of concerns between service layers
Set up environment-based configuration for flexibility
Created a scalable foundation for future enhancements
Overall, implementing this service provided valuable experience in working with Large Language Models, API design, Docker deployment, and system integration. The resulting system demonstrates practical application of modern AI services while maintaining code quality and system reliability.

I implemented OPEA in two stages:

- Infrastructure Setup:
1. Deployed Ollama LLM service using Docker Compose on port 8008.
2. Integrated the llama3.2:1b model within the Docker container.
3. Configured environment variables for proper service operation.

- Service Development:
1. Developed a FastAPI service with a /v1/example-service endpoint for chat completion requests.
2. Implemented message formatting and response handling for communication with Ollama.
3. Included error handling and logging for reliability.

Testing and Verification
1. Direct API Testing: Verified Ollama functionality through direct API calls.
Service Integration: Tested FastAPI service endpoints for correct interaction with Ollama.
2. Response Handling: Ensured proper handling of streaming responses and error conditions.
(https://github.com/AC888221/free-genai-bootcamp-2025/blob/main/opea-comps/Readme.md)
