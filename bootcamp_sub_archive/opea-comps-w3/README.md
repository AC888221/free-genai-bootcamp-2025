# OPEA-Comps: Megaservice

## Quick Links
- [Visual Feature Showcase](Showcase_Megaservice.md) - See the service in action with screenshots and usage examples
- [Bootcamp Week 3: Implementation Report](#bootcamp-week-3-opea-megaservice-implementation-report)
- [LLM Megaservice Glossary](#llm-megaservice-glossory)

## MegaService

MegaService is a comprehensive AI service that combines large language model (LLM) capabilities with text-to-speech (TTS) functionality, providing a complete solution for conversational AI applications.

### Overview

MegaService integrates a FastAPI backend with a Streamlit frontend to deliver a user-friendly interface for interacting with AI models. The service uses Qwen2.5 as the language model and GPT-SoVITS for text-to-speech conversion.

### Architecture

The service consists of several components:
- **FastAPI Server**: Handles API requests and orchestrates the interaction between components (runs on port 9500)
- **Streamlit Frontend**: Provides a web interface for user interaction (runs on port 8501)
- **LLM Integration**: Connects to a vLLM-powered language model (runs on port 8008)
- **TTS Service**: Integrates with GPT-SoVITS for high-quality speech synthesis (runs on ports 9088/9880)

### Features

- Real-time text generation using state-of-the-art language models.
- High-quality text-to-speech conversion.
- Multilingual support with a focus on Chinese (Putonghua).
- Containerized deployment for easy scaling and management.
- Health monitoring and logging.

### Configuration

The service is configured through environment variables in the `.env` file. Key configurations include:

```env
# LLM Configuration
LLM_MODEL_ID="Qwen/Qwen2.5-0.5B-Instruct"
LLM_ENDPOINT_PORT=8008
LLM_ENDPOINT="http://${host_ip}:${LLM_ENDPOINT_PORT}"

# TTS Configuration
TTS_PORT=9088
GPT_SOVITS_PORT=9880
TTS_ENDPOINT=http://tts-gptsovits-service:9088
```

### Deployment

#### Prerequisites

- Docker and Docker Compose
- Python 3.10+
- Hugging Face token for model access

#### Running with Docker

The service is containerized and can be deployed using Docker:

```bash
docker-compose up
```

#### Local Development

For local development:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```
3. Run the Streamlit frontend:
   ```bash
   streamlit run frontend/app.py
   ```

### Testing

The repository includes a test scripts for testing the MegaService and GPT-SoVITS TTS component end points and functionality.

### Troubleshooting

#### Common Issues

##### TTS Service Connection Issues

If you see errors like `TTS health check failed` or `Temporary failure in name resolution`, check:
- The TTS service is running and accessible.
- The hostname in `TTS_ENDPOINT` is correctly configured and resolvable.
- Network connectivity between the MegaService container and the TTS service.

##### LLM Service Issues

If the language model is not responding:
- Verify the LLM service is running.
- Check the `LLM_ENDPOINT` configuration.
- Ensure the model specified in `LLM_MODEL_ID` is correctly loaded.

### Logs

The servicOPEA Comps (Week 3)e maintains detailed logs in the `logs` directory:
- `server.log`: FastAPI server logs.
- `streamlit.log`: Frontend application logs.
- `vllm.log`: Language model service logs.

#### Known Issues

- The TTS and LLM services are often often flagged as not healty.
- Despite health check failures, the Streamlit frontend has been able to generate audio responses

### Container Structure

The application consists of multiple containers:
1. **MegaService container**: Main service with FastAPI and Streamlit
2. **TTS-GPTSoVITS service**: Handles text-to-speech conversion
3. **vLLM service**: Provides language model capabilities

Each container has its own health checks and endpoints.

### Development

#### Updating the Frontend

For quick updates to the Streamlit frontend during development, use the provided script. This script copies the updated `MegaTalk.py` file to the running container and restarts the Streamlit application.

```bash
./update_megatalk.sh
```

## Bootcamp Week 3: OPEA Megaservice Implementation Report

In week 1, I set up Ollama 2.1 B, so for this week I focused on vLLM.

This is a table of the supported vLLM models (from 08/03/2025, source: https://docs.vllm.ai/en/latest/models/supported_models.html#) that I found had a RAM requirement of 16GB or less:

```markdown
| Architecture                  | Models                        | RAM Requirement | Storage Requirement | Release Date |
|-------------------------------|-------------------------------|-----------------|---------------------|--------------|
| ArcticForCausalLM             | Arctic                        | 16GB            | 50GB                | 2024-01-15   |
| BartForConditionalGeneration  | BART                          | 16GB            | 20GB                | 2020-06-25   |
| DbrxForCausalLM               | DBRX                          | 16GB            | 30GB                | 2023-05-10   |
| GPT2LMHeadModel               | GPT-2                         | 16GB            | 10GB                | 2019-02-14   |
| MambaForCausalLM              | Mamba                         | 16GB            | 25GB                | 2023-11-20   |
| MiniCPMForCausalLM            | MiniCPM                       | 16GB            | 40GB                | 2022-08-30   |
| OLMoForCausalLM               | OLMo                          | 16GB            | 15GB                | 2023-03-18   |
| Phi3SmallForCausalLM          | Phi-3-Small                   | 16GB            | 20GB                | 2024-07-22   |
```

### OPEA Development Progress Summary

#### Initial Setup and Model Selection for vLLM

- Analyzed vLLM supported models with lower RAM requirements (targeting ≤16GB)
- Created comparison table of 8 model architectures but was unable to successfully run any of the shortlisted models
- Successfully switched to Qwen/Qwen2.5-0.5B-Instruct after seeing Discord comments from user Dmytro, but it still took over 10 minutes to load.

#### Technical Configuration of vLLM

- Updated docker-compose.yml for vllm-openvino (CPU support)
- Consolidated configuration in .env file for better management
- Fixed case sensitivity issues in OpenVINO-related variables
- Added essential environment variables for OpenVINO GPU support
- Corrected configuration settings, including max_model_len setting from initial problematic value of just 1 token to 2048

#### ChatQnA and GPT-SoVITS Service Integration

- Successfully migrated FastAPI from Ollama to VLLM service
- Updated API endpoints from Ollama-specific to OpenAI-compatible format
- Developed MegaService to orchestrate both LLM and TTS functionalities
- Integrated GPT-SoVITS for text-to-speech capabilities
- Created dedicated debug endpoint (/debug/tts-info) for TTS configuration inspection
- Created a Dockerfile for MegaService to define the build process, including dependencies and entry point
- Integrated MegaService into docker-compose.yaml for easy deployment
- Developed update_megatalk.sh to automate copying MegaTalk.py into the Docker container and restarting Streamlit, ensuring efficient handling and quick iterations without rebuilding the container

#### Error Handling and Robustness

- Implemented fallback mechanism to try multiple TTS endpoints
- Added comprehensive error handling for both LLM and TTS to ensure graceful failures
- Enhanced logging with detailed request/response information, including payload formats and responses
- Set up rotating log files to manage disk space effectively
- Extended timeout values to accommodate model loading and processing times
- Created a test script to test endpoints for all the components of the MegaService

#### User Interface Development

- Implemented Streamlit frontend (MegaTalk.py) for user interaction
- Added audio file saving in /audio directory with playback functionality
- Developed column layout for improved conversation history display
- Created update_megatalk.sh script to streamline development workflow
- Added Chinese language support with HSK level selection (HSK 1-6)
- Implemented detailed HSK-specific prompts with vocabulary and grammar guidelines
- Created system prompts to enforce language-specific responses

#### Key Takeaways

- OpenVINO configuration required specific case-sensitive settings
- The trust_remote_code=True flag in docker-compose files was necessary for the Hugging Face Transformers library to load models with custom code from their repository on the Hugging Face Hub
- Timeouts had to be extended for health checks and requests were extended due to the long model loading and processing times on my hardware.
- Direct service communication was more efficient than unnecessary wrapper services
- Robust error handling and detailed logging were essential for debugging distributed services
- Environment variable consolidation improved consistency and maintainability
- Developing scripts to automate the deployment and development workflow was a great way to streamline the development process and reduce the amount of time it took to make changes

## Appendices

### LLM Megaservice Glossory

LLM: An LLM (Large Language Model) is an AI model designed to understand and generate human-like text based on extensive training data.
LLM microservices: These are essentially containerized versions of large language models (LLMs). They package the model and its dependencies into a container, ensuring consistency and ease of deployment across different environments.
Ollama (LLM) microservice: This is a service developed by LlamaFactory.  It is a toolkit designed for deploying and serving LLMs, particularly locally. It containerizes LLMs and provides tools to enhance their performance, scalability, and flexibility. The models it supports include Llama, Mistral, Nemo, Firefunction v2, and Command-R.
TGI (Text Generation Inference) LLM Microservice: This is a service developed by Hugging Face. It is a toolkit that containrizes LLMs and provides tools to enhance their performance, scalability, and flexibility. The models it supports include Llama, Falcon, StarCoder, BLOOM, GPT-NeoX, and T5. 
vLLM: This is a service originally developed by Sky Computing Lab at UC Berkeley that has since evolved into a community-driven project. It is a toolkit that containrizes LLMs and provides tools to enhance their performance, scalability, and flexibility. It also supports ditributed inference. The models it supports include Llama, Mistral, Falcon, StarCoder, BLOOM, GPT-NeoX, and many more. 
LLM megaservice: An LLM megaservice refers to a comprehensive service that integrates multiple microservices related to large language models (LLMs) into a single, cohesive system.