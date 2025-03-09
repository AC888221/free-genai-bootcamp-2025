## Testing the FastAPI Application

### 1. Install Dependencies
Ensure all required dependencies are installed with the following command:

```bash
pip install fastapi httpx uvicorn python-dotenv
```

### 2. Start the VLLM Service
Ensure the `vllm` service is running by starting it with Docker Compose:

```bash
cd /path/to/opea-comps-w3
docker-compose up
```

Verify that the `vllm` service is running without errors.

### 3. Start the FastAPI Application
In a separate terminal, navigate to the FastAPI application directory and start it with Uvicorn:

```bash
cd /path/to/opea-comps-w3/ChatQnA
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

- `app:app` refers to the `app` instance in the `app.py` file.
- The `--reload` flag enables automatic reloading of the server upon code changes.

### 4. Test the API Endpoints
Testing the FastAPI application can be done using tools like **cURL**, **Postman**, or **HTTPie**. Here’s an example using cURL:

#### Example Request
Send a POST request to the `/v1/example-service` endpoint with a JSON payload:

```bash
curl -X POST "http://localhost:8000/v1/example-service" \
-H "Content-Type: application/json" \
-d '{
    "model": "Qwen/Qwen2.5-0.5B-Instruct",
    "messages": [{"role": "user", "content": "What is the capital of France?"}]
}'
```

### 5. Validate the Response
Check the response from the API call. A JSON response containing the assistant's message based on the input provided should be received.
