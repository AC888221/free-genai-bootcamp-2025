

# OPEA Development Progress Summary
## Initial Setup and Model Selection for vLLM

- Analyzed vLLM supported models with lower RAM requirements (targeting ≤16GB)
- Created comparison table of 8 model architectures but was unable to successfully run any of the shortlisted models
- Successfully switched to Qwen/Qwen2.5-0.5B-Instruct after seeing Discord comments from user Dmytro, but it still took over 10 minutes to load.

## Technical Configuration of vLLM

- Updated docker-compose.yml for vllm-openvino (CPU support)
- Consolidated configuration in .env file for better management
- Fixed case sensitivity issues in OpenVINO-related variables
- Added essential environment variables for OpenVINO GPU support
- Corrected configuration settings, including max_model_len setting from initial problematic value of just 1 token to 2048

## ChatQnA and GPT-SoVITS Service Integration

- Successfully migrated FastAPI from Ollama to VLLM service
- Updated API endpoints from Ollama-specific to OpenAI-compatible format
- Developed MegaService to orchestrate both LLM and TTS functionalities
- Integrated GPT-SoVITS for text-to-speech capabilities
- Created dedicated debug endpoint (/debug/tts-info) for TTS configuration inspection
- Created a Dockerfile for MegaService to define the build process, including dependencies and entry point
- Integrated MegaService into docker-compose.yaml for easy deployment
- Developed update_megatalk.sh to automate copying MegaTalk.py into the Docker container and restarting Streamlit, ensuring efficient handling and quick iterations without rebuilding the container

## Error Handling and Robustness

- Implemented fallback mechanism to try multiple TTS endpoints
- Added comprehensive error handling for both LLM and TTS to ensure graceful failures
- Enhanced logging with detailed request/response information, including payload formats and responses
- Set up rotating log files to manage disk space effectively
- Extended timeout values to accommodate model loading and processing times
- Created a test script to test endpoints for all the components of the MegaService

## User Interface Development

- Implemented Streamlit frontend (MegaTalk.py) for user interaction
- Added audio file saving in /audio directory with playback functionality
- Developed column layout for improved conversation history display
- Created update_megatalk.sh script to streamline development workflow
- Added Chinese language support with HSK level selection (HSK 1-6)
- Implemented detailed HSK-specific prompts with vocabulary and grammar guidelines
- Created system prompts to enforce language-specific responses

## Key Takeaways

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
