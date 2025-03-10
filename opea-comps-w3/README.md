OPEA Comps (Week 3)

In week 1, I set up Ollama 2.1 B


This is a table of the supported vLLM models (from 08/03/2025, source: https://docs.vllm.ai/en/latest/models/supported_models.html#) that had a RAM requirement of 16GB or less:

```markdown
| Architecture                  | Models                        | Example HF Models                                                                 | RAM Requirement | Storage Requirement | Release Date |
|-------------------------------|-------------------------------|----------------------------------------------------------------------------------|-----------------|---------------------|--------------|
| ArcticForCausalLM             | Arctic                        | Snowflake/snowflake-arctic-base, Snowflake/snowflake-arctic-instruct, etc.       | 16GB            | 50GB                | 2024-01-15   |
| BartForConditionalGeneration  | BART                          | facebook/bart-base, facebook/bart-large-cnn, etc.                                | 16GB            | 20GB                | 2020-06-25   |
| DbrxForCausalLM               | DBRX                          | databricks/dbrx-base, databricks/dbrx-instruct, etc.                             | 16GB            | 30GB                | 2023-05-10   |
| GPT2LMHeadModel               | GPT-2                         | gpt2, gpt2-xl, etc.                                                              | 16GB            | 10GB                | 2019-02-14   |
| MambaForCausalLM              | Mamba                         | state-spaces/mamba-130m-hf, state-spaces/mamba-790m-hf, state-spaces/mamba-2.8b-hf, etc. | 16GB            | 25GB                | 2023-11-20   |
| MiniCPMForCausalLM            | MiniCPM                       | openbmb/MiniCPM-2B-sft-bf16, openbmb/MiniCPM-2B-dpo-bf16, openbmb/MiniCPM-S-1B-sft, etc. | 16GB            | 40GB                | 2022-08-30   |
| OLMoForCausalLM               | OLMo                          | allenai/OLMo-1B-hf, allenai/OLMo-7B-hf, etc.                                     | 16GB            | 15GB                | 2023-03-18   |
| Phi3SmallForCausalLM          | Phi-3-Small                   | microsoft/Phi-3-small-8k-instruct, microsoft/Phi-3-small-128k-instruct, etc.     | 16GB            | 20GB                | 2024-07-22   |
```
 ArcticForCausalLM
 Phi3SmallForCausalLM  
Based on this information, I selected Phi3SmallForCausalLM as it was realtively new and required less storage.

As vLLM is a community-driven project, I think that the model ID will come from a community type source like Hugging Face.
irst, let's update your docker-compose.yml to use vllm-openvino instead of vllm-server since you're running on CPU:
t looks like the DBRX model is gated, meaning it requires special access permissions even with your HF token. Let's try a different model that's publicly available. Let's use GPT


microsoft/Phi-3-small-8k-instruct model requires the trust_remote_code=True flag to be set.  This flag is necessary for models whose code lives on the Hugging Face hub rather than being natively available in the Transformers library.

Dmytro
OP
 — 3/2/2025 8:52 PM
"Thank you for a great suggestion - I was looking for logs, but loading progress is definitely isn't logged. I have switched to the smallest possible model - Qwen/Qwen2.5-0.5B-Instruct and it worked. Took 10 min or so to fully load."


added this to the docker_compose.yaml file:
    command: --model $LLM_MODEL_ID --host 0.0.0.0 --port 80 --trust-remote-code

Update your .env file to ensure proper paths:

rst, let's update your docker-compose.yml to use vllm-openvino ins
docker-compose -f docker_compose.yaml up vllm-openvino


# Install vLLM from pip:
pip install vllm

Copy
# Load and run the model:
vllm serve "microsoft/Phi-3-small-8k-instruct"

Copy
# Call the server using curl:
curl -X POST "http://localhost:8000/v1/chat/completions" \
	-H "Content-Type: application/json" \
	--data '{
		"model": "microsoft/Phi-3-small-8k-instruct",
		"messages": [
			{
				"role": "user",
				"content": "What is the capital of France?"
			}
		]
	}'

Create a README.md file that explains:
The purpose of each service
Hardware requirements for each option
How to choose the right service for different environments
Step-by-step instructions for starting each service
3. Provide Example Profiles
Create example profiles for different common scenarios:
# CPU-only profile
LLM_ENDPOINT_PORT=8008
LLM_MODEL_ID=Qwen/Qwen2.5-0.5B-Instruct
# OpenVINO CPU profile
LLM_ENDPOINT_PORT=8008
LLM_MODEL_ID=Qwen/Qwen2.5-0.5B-Instruct
VLLM_OPENVINO_DEVICE=CPU
# OpenVINO Arc GPU profile
LLM_ENDPOINT_PORT=8008
LLM_MODEL_ID=Qwen/Qwen2.5-0.5B-Instruct
VLLM_OPENVINO_DEVICE=GPU
RENDER_GROUP_ID=110

vllm 15 mins

WARN[0000] The "http_proxy" variable is not set. Defaulting to a blank string.
WARN[0000] The "https_proxy" variable is not set. Defaulting to a blank string.
WARN[0000] The "no_proxy" variable is not set. Defaulting to a blank string.
WARN[0000] The "http_proxy" variable is not set. Defaulting to a blank string.
WARN[0000] The "no_proxy" variable is not set. Defaulting to a blank string.
WARN[0000] The "https_proxy" variable is not set. Defaulting to a blank string.
WARN[0000] The "http_proxy" variable is not set. Defaulting to a blank string.
WARN[0000] The "https_proxy" variable is not set. Defaulting to a blank string.
WARN[0000] The "http_proxy" variable is not set. Defaulting to a blank string.
WARN[0000] The "https_proxy" variable is not set. Defaulting to a blank string.


### Updated `README.md`

```markdown
### Download (pull) a model

To pull a model from the VLLM service, use the following command:

```bash
curl http://localhost:8008/api/pull -d '{
"model": "Qwen/Qwen2.5-0.5B-Instruct"
}'
```

### Generate a Request

To generate a response using the VLLM service, use the following command:

```bash
curl http://localhost:8008/api/generate -d '{
"model": "Qwen/Qwen2.5-0.5B-Instruct",
"prompt": "Why is the sky blue?"
}'
```

## Port change for Megaservice

If you need to change the port for the megaservice, you can use the following command:

```bash
HOST_IP=$(hostname -I | awk '{print $1}') NO_PROXY=localhost LLM_ENDPOINT_PORT=9000 LLM_MODEL_ID="Qwen/Qwen2.5-0.5B-Instruct" docker-compose up
```

### Download (pull) a model

To pull a model from the megaservice, use the following command:

```bash
curl http://localhost:9000/api/pull -d '{
"model": "Qwen/Qwen2.5-0.5B-Instruct"
}'
```

### Generate a Request

To generate a response using the megaservice, use the following command:

```bash
curl http://localhost:9000/api/generate -d '{
"model": "Qwen/Qwen2.5-0.5B-Instruct",
"prompt": "Why is the sky blue?"
}'
```

TTS Services Status
GPT-SoVITS Service
Status: Running successfully on port 9880
Container: gpt-sovits-service
Health Check: Passing (returning 200 OK responses)
Model Information:
Using default SoVITS model: GPT_SoVITS/pretrained_models/s2G488k.pth
Using default GPT model: GPT_SoVITS/pretrained_models/s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt
Default reference audio: ./welcome_cn.wav (Chinese welcome message)
Model version: v1
Parameter count: 77.49M
TTS Frontend Service
Status: Running successfully on port 9088
Container: tts-gptsovits-service
Connected to: GPT-SoVITS service at 172.20.0.3

How to Use These Services
You can now interact with the TTS system through the frontend service:
Text-to-Speech API: Available at http://localhost:9088/tts
You can send POST requests with text to convert to speech
Health Check: Available at http://localhost:9088/health and http://localhost:9880/health
Both are returning 200 OK responses, indicating the services are healthy

Perfect! Now I can see the correct endpoint from the OpenAPI documentation. According to the OpenAPI JSON you shared, the correct endpoint for text-to-speech is:

And it expects a request body with this structure:

{
  "input": "Hello, this is a test.",
  "model": "microsoft/speecht5_tts",
  "voice": "default",
  "response_format": "mp3",
  "speed": 1.0
}
Let's try using this endpoint with the correct request format:

curl -X POST "http://localhost:9088/v1/audio/speech" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hello, this is a test.",
    "model": "microsoft/speecht5_tts",
    "voice": "default",
    "response_format": "mp3",
    "speed": 1.0
  }'

If you want to save the audio output to a file, you can use:
curl -X POST "http://localhost:9088/v1/audio/speech" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hello, this is a test.",
    "model": "microsoft/speecht5_tts",
    "voice": "default",
    "response_format": "mp3",
    "speed": 1.0
  }' \
  --output test_speech.mp3





















## Appendices

### LLM Megaservice Glossory

LLM: An LLM (Large Language Model) is an AI model designed to understand and generate human-like text based on extensive training data.
LLM microservices: These are essentially containerized versions of large language models (LLMs). They package the model and its dependencies into a container, ensuring consistency and ease of deployment across different environments.
Ollama (LLM) microservice: This is a service developed by LlamaFactory.  It is a toolkit designed for deploying and serving LLMs, particularly locally. It containerizes LLMs and provides tools to enhance their performance, scalability, and flexibility. The models it supports include Llama, Mistral, Nemo, Firefunction v2, and Command-R.
TGI (Text Generation Inference) LLM Microservice: This is a service developed by Hugging Face. It is a toolkit that containrizes LLMs and provides tools to enhance their performance, scalability, and flexibility. The models it supports include Llama, Falcon, StarCoder, BLOOM, GPT-NeoX, and T5. 
vLLM: This is a service originally developed by Sky Computing Lab at UC Berkeley that has since evolved into a community-driven project. It is a toolkit that containrizes LLMs and provides tools to enhance their performance, scalability, and flexibility. It also supports ditributed inference. The models it supports include Llama, Mistral, Falcon, StarCoder, BLOOM, GPT-NeoX, and many more. 
LLM megaservice: An LLM megaservice refers to a comprehensive service that integrates multiple microservices related to large language models (LLMs) into a single, cohesive system.
