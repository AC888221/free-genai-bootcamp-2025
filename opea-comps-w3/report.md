Initial Research and Model Selection:
Analyzed vLLM supported models with RAM requirements of 16GB or less
Created a comprehensive comparison table of 8 model architectures
Initially selected Phi3SmallForCausalLM due to its newness and lower storage requirements
Implementation Attempts:
Tried to implement vLLM with microsoft/Phi-3-small-8k-instruct model
Encountered issues requiring trust_remote_code=True flag
Switched to a smaller model (Qwen/Qwen2.5-0.5B-Instruct) which successfully loaded in about 10 minutes
Technical Setup:
Updated docker-compose.yml to use vllm-openvino (for CPU support)
Added configuration command with trust-remote-code flag
Attempted model deployment using both Docker and pip installation methods
Tested API endpoints using curl commands
Documentation:
Created a glossary of LLM-related terms
Documented different LLM microservices (Ollama, TGI, vLLM)
Recorded implementation challenges and solutions


Initial Problem Identification:
Discovered issues with model loading and configuration
Found that the system was defaulting to GPT-2 instead of the intended Qwen model
Identified that the max_model_len setting was causing conflicts
Model Selection:
Switched to a smaller, more efficient model: Qwen/Qwen2.5-0.5B-Instruct
Added proper trust_remote_code support for Qwen models
Adjusted max_model_len to 1024 to match model capabilities
Configuration Improvements:
Consolidated configuration in .env file for better management
Added essential environment variables:
OpenVINO GPU support
Model quantization settings
HuggingFace token and cache settings
Long model length allowance
Docker Configuration Updates:
Removed unnecessary services (vllm-gaudi-server)
Optimized vllm-openvino-arc service for Intel GPU usage
Added proper device mappings for GPU access
Improved healthcheck configuration
Added proper environment variable passing from .env
System Requirements:
Configured for Intel integrated GPU usage
Set up proper OpenVINO backend settings
Added necessary device access permissions
The system should now be better configured for:
Lower resource usage (smaller model)
Better GPU utilization (OpenVINO optimizations)
Easier configuration management (.env file)
More reliable startup and operation


Here's a summary of the actions taken to set up and test the OPEA (OpenAI-based) API using the vLLM framework:
Setup and Configuration
1. Docker Compose Configuration:
Created a docker-compose.yaml file to define the services, including vllm-server, vllm-openvino, and vllm-openvino-arc.
Configured environment variables and port mappings to ensure proper operation.
Environment Variables:
Set environment variables for model configuration, including LLM_MODEL_ID, LLM_ENDPOINT_PORT, and others to customize the behavior of the services.
Service Initialization:
Started the Docker containers using Docker Compose, which pulled the necessary images and initialized the services.
Testing and Validation
4. Health Check:
Attempted to check the health of the API using curl http://localhost:8008/health, which did not return output initially.
5. API Functionality Testing:
Successfully tested the chat completion endpoint with a request for a joke, receiving a valid response.
Successfully tested the text completion endpoint with a prompt, receiving a coherent continuation of the text.
6. Log Monitoring:
Monitored logs for the vllm-openvino-arc container to identify any warnings or errors during startup and operation.
Noted deprecation warnings related to the websockets library but confirmed that they did not affect functionality.
Observations
The API is operational and responding to requests, indicating successful deployment and configuration.
The health check endpoint may require further investigation, as it did not return output despite the API functioning correctly.
Next Steps
Continue testing additional endpoints to explore the full capabilities of the API.
Investigate the health check issue further if needed.
Consider integrating the API into applications or workflows as required.
This summary encapsulates the progress made with the OPEA project, highlighting the successful setup and testing of the API services. If you need any further details or specific information, feel free to ask!