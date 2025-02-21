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

Q: Does bridge mode mean we can only access Ollama API with another model in the docker compose?
A: No, the host machine will be able to access it.

Q: Which port is being mapped 8008->11434
A: In this case 8008 is the port that the hose machine will access. The other port is the guest port (the port of the service inside the container)

Q: If we pass the LLM_Model_Id to the Ollama server will it download the model when on start?
A: It does not appear so. The Ollama CLI might be running multiple APIs so you need to call the /pull api before trying to generate text.

Q: Will the model be downloaded in the container? Does that mean the model will be deleted when the container stops running?

Q: If we pass the LLM_Model_Id to the Ollama server will it ?
A: We pass it to the docker compose file.

The model will download into the container, and vanish when the containr stops running. You need to mount a local drive and there is probably more work to be done.

