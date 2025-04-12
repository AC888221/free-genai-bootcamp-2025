# Implementing OPEA Comps (Generative AI Components)

[View Implementation Showcase](Showcase_Opea-comps.md)

[Jump to Bootcamp Week 1: OPEA Implementation Report](https://github.com/AC888221/free-genai-bootcamp-2025/blob/main/opea-comps/README.md#bootcamp-week-1-opea-implementation-report)

[Jump to LLM Megaservice Glossory](https://github.com/AC888221/free-genai-bootcamp-2025/blob/main/opea-comps/README.md#llm-megaservice-glossory)

## Running Ollama Third-Party Services

### Choosing a Model

Get the model_id that Ollama will launch from the [Ollama Library](https://ollama.com/library).

Example: [llama3.2](https://ollama.com/library/1lama3.2)

### Getting the Host IP

#### Linux

Get your IP address
```sh
sudo apt install net-tool
if config
```

Or you can try this

HOST_IP=$(hostname -I | awk '{print $1}') NO_PROXY=localhost LLM_ENDPOINT_PORT=8008 LLM_MODEL_ID="1lama3.2:1b" dockercompose up

## Using the Ollama API

Once the Ollama server is running, make API calls to the [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md).

### Download (pull) a model

curl http://localhost:8008/api/pull -d '{
    "model": "llama3.2:1b"
}'

### Generate a Request

curl http://localhost:8008/api/generate -d '{
    "model": "llama3.2:1b",
    "prompt": "Why is the sky blue?"
}'

## Port change for Megaservice
HOST_IP=$(hostname -I | awk '{print $1}') NO_PROXY=localhost LLM_ENDPOINT_PORT=9000 LLM_MODEL_ID="1lama3.2:1b" dockercompose up

### Download (pull) a model

curl http://localhost:9000/api/pull -d '{
    "model": "llama3.2:1b"
}'

### Generate a Request

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

## Bootcamp Week 1: OPEA Implementation Report

### Architecture Overview
- **Three-tier architecture**: Client → FastAPI Service → Ollama (LLM)
- **Separation of concerns**: Maintained clear boundaries between service layers
- **Environment-based configuration**: Ensured flexibility and adaptability
- **Scalable foundation**: Created a robust base for future enhancements

### Implementation Stages

#### Infrastructure Setup
1. **Deployed Ollama LLM service**: Using Docker Compose on port 8008
2. **Integrated the llama3.2:1b model**: Within the Docker container
3. **Configured environment variables**: For proper service operation

#### Service Development
1. **Developed a FastAPI service**: With a `/v1/example-service` endpoint for chat completion requests
2. **Implemented message formatting and response handling**: For communication with Ollama
3. **Included error handling and logging**: To ensure reliability

### Testing and Verification
1. **Direct API Testing**: Verified Ollama functionality through direct API calls
2. **Service Integration**: Tested FastAPI service endpoints for correct interaction with Ollama
3. **Response Handling**: Ensured proper handling of streaming responses and error conditions

## Appendices

### LLM Megaservice Glossory

LLM: An LLM (Large Language Model) is an AI model designed to understand and generate human-like text based on extensive training data.
vLLMs: vLLMs are a tool that helps run large language models quickly and efficiently, using less memory. They are high-throughput, memory-efficient engines for serving large language models with advanced features like PagedAttention and continuous batching.
LLM microservices: LLM microservices are essentially containerized versions of large language models (LLMs). They package the model and its dependencies into a container, ensuring consistency and ease of deployment across different environments.
LLM megaservice: An LLM megaservice refers to a comprehensive service that integrates multiple microservices related to large language models (LLMs) into a single, cohesive system.
TGI LLM Microservice: TGI (Text Generation Inference) LLM Microservice is a specific service developed by Hugging Face, not a general term for LLM microservices. It is a toolkit designed for deploying and serving large language models (LLMs).  It enhances performance, scalability, and flexibility, making it easier to integrate LLMs into various applications and handle high-throughput requests.
Quantization is a technique used to reduce the size and memory usage of machine learning models by representing the model's weights and activations with lower precision. Here's a simple explanation: