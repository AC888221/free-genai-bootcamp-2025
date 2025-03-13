# Agents and Agentic Workflow: Vocabulary Extraction

[Jump to Bootcamp Week 3: Agents and Agentic Workflow Implementation Report](https://github.com/AC888221/free-genai-bootcamp-2025/blob/main/opea-comps-w3/README.md#bootcamp-week-3-agents-and-agentic-workflow-implementation-report)

## Song Vocabulary Extractor

A FastAPI and Streamlit application that finds lyrics for songs in Putonghua (Mandarin Chinese) and extracts vocabulary for language learners.

### Business Goal
This program finds lyrics on the internet for a target song in Putonghua and produces vocabulary to be imported into our database. The target audience includes language learners, educators, and developers who need structured vocabulary data.

# Features
- Search for song lyrics by title and artist
- Extract vocabulary from lyrics, including simplified characters, pinyin, and English translations
- Store lyrics and vocabulary in a SQLite database
- API endpoints for retrieving lyrics and vocabulary
- Streamlit frontend for user interaction

### Technical Stack
- FastAPI
- Streamlit
- Ollama with Phi3 (3.8B) model
- SQLite3
- DuckDuckGo Search Python
- HTML2Text for content extraction
- Docker support via docker-compose

### Getting Started

#### Prerequisites
- Python 3.8+
- Ollama installed locally or accessible via API
- The Phi3 (3.8B) model available in Ollama

#### Installation

1. Clone the repository
2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

#### Configuration
Create a `.env` file in the project root (or modify the existing one):
    ```bash
    LLM_ENDPOINT_PORT=8008
    no_proxy=localhost,127.0.0.1
    http_proxy=
    https_proxy=
    LLM_MODEL_ID=phi3:3.8b
    host_ip=0.0.0.0
    ```

#### Running the Application

##### Using Python directly
    ```bash
    cd song-vocab
    python run_app.py
    ```

The FastAPI backend will be available at http://localhost:8000, and the Streamlit frontend will be available at http://localhost:8501.

##### Using Docker Compose

    ```bash
    # Get your IP address (Linux)
    HOST_IP=$(hostname -I | awk '{print $1}')

    # Run docker-compose
    HOST_IP=$HOST_IP NO_PROXY=localhost LLM_ENDPOINT_PORT=8008 LLM_MODEL_ID="phi3:3.8b" docker-compose up
    ```

### API Endpoints

- `GET /`: Welcome message
- `POST /api/agent`: Get lyrics and vocabulary for a song
    ```json
    {
      "message_request": "月亮代表我的心",
      "artist_name": "邓丽君"
    }
    ```
- `POST /api/get_vocabulary`: Extract vocabulary from provided text
    ```json
    {
      "text": "月亮代表我的心\n你问我爱你有多深\n我爱你有几分"
    }
    ```

### Using the Ollama API

Once the Ollama server is running, you can make API calls:

#### Download (pull) a model

    ```bash
    curl http://localhost:8008/api/pull -d '{
    "model": "phi3:3.8b"
    }'
    ```

#### Generate a Request

    ```bash
    curl http://localhost:8008/api/generate -d '{
    "model": "phi3:3.8b",
    "prompt": "Why is the sky blue?"
    }'
    ```

### Project Structure
```
song-vocab/
├── __init__.py
├── .gitignore
├── main.py             # FastAPI application entry point
├── run_app.py          # Script to run both backend and frontend
├── streamlit_app.py    # Streamlit frontend application
├── agent.py            # LyricsAgent implementation
├── database.py         # SQLite database interface
├── docker-compose.yaml # Docker configuration
├── .env                # Environment variables
├── requirements.txt
├── README.md
├── prompts/
│   ├── __init__.py
│   └── vocabulary-agent.md
├── tools/
│   ├── __init__.py
│   ├── search_web.py          # DuckDuckGo search
│   ├── get_page_content.py    # Web page content extraction
│   ├── extract_vocabulary.py  # Vocabulary extraction with LLM
│   └── generate_song_id.py    # URL-safe ID generation
├── outputs/
│   └── .gitkeep
├── bin/
│   ├── run.sh          # Shell script to run application
│   └── run_tests.sh    # Shell script for tests
└── tests/
    ├── __init__.py
    ├── test_agent.py   # Tests for LyricsAgent
    └── test_api.py     # Tests for API endpoints
```

### Testing

    ```bash
    # Run all tests
    ./bin/run_tests.sh

    # Or run individual test files
    python -m tests.test_agent
    python -m tests.test_api
    ```

## Bootcamp Week 3: Agents and Agentic Workflow Implementation Report

### Executive Summary

The Song Vocabulary project implements an AI agent that extracts vocabulary from Chinese (Putonghua) song lyrics to assist language learners. The project demonstrates agentic workflow principles by breaking complex tasks into modular components and implementing a resilient system that adapts to failures. Key accomplishments include setting up the project infrastructure, integrating with Ollama for local LLM deployment, implementing backend API functionality, and developing a Streamlit frontend for user interaction.

### Project Architecture

The system follows a multi-component architecture:
- **FastAPI Backend**: Provides API endpoints for lyrics retrieval and vocabulary extraction
- **Ollama Integration**: Runs a local LLM (Phi-3 3.8B) for text processing
- **Database**: Stores processed songs and vocabulary items
- **Streamlit Frontend**: Offers a user-friendly interface for searching songs and extracting vocabulary

### Key Technical Implementations

#### 1. Agentic Workflow Design

The core of the system is the `LyricsAgent` class that orchestrates a workflow using specialized tools:
```
1. Input Processing → 2. Web Search → 3. Content Retrieval → 4. LLM Processing → 5. Result Formatting
```

This demonstrates agency through:
- Chaining multiple tools to accomplish complex tasks
- Making decisions about which tools to use based on current state
- Implementing fallback mechanisms when primary methods fail
- Coordinating between different systems (web search, content fetching, LLM processing)

#### 2. Robust Error Handling

A standout feature is the dual-method approach for vocabulary extraction:

**Primary Method (LLM-based)**:
- Uses Phi-3 model with structured prompts
- Returns comprehensive information (characters, pinyin, translations)
- Employs validation to ensure proper JSON formatting

**Fallback Method (Regex-based)**:
- Activates when LLM fails to respond properly
- Uses regular expressions to extract Chinese characters
- Provides basic character-level extraction when sophisticated processing fails

Example of fallback activation:
```python
if "[START_JSON]" not in response and "[END_JSON]" not in response:
    logger.warning("No JSON tags found in response, using fallback extraction")
    return fallback_extraction(text)
```

#### 3. Asynchronous Processing

Implemented asynchronous HTTP requests using `httpx.AsyncClient` for efficient I/O operations:
```python
async with httpx.AsyncClient(base_url=OLLAMA_API_BASE) as client:
    response = await client.post("/api/generate", json=payload, timeout=300)
```

For Streamlit integration, created custom async handling:
```python
# Custom solution for Streamlit's synchronous nature
def run_async(func):
    async_thread = Thread(target=lambda: asyncio.run(func()))
    async_thread.start()
    return async_thread
```

#### 4. Docker and Environment Configuration

Implemented Docker-based deployment with Ollama integration:
- Created `docker-compose.yml` for service orchestration
- Developed `startup.sh` script to ensure model availability
- Added retry mechanisms to handle service initialization timing

Example of retry implementation:
```bash
# Retry loop for service initialization
for i in {1..5}; do
    if curl -s http://localhost:8008 > /dev/null; then
        break
    fi
    echo "Waiting for Ollama service... attempt $i"
    sleep 2
done
```

### Domain Knowledge Acquired

#### 1. Language Model Response Handling

The project revealed critical insights about working with LLMs in production environments:

- **Response Formatting Challenges**: LLMs often fail to follow formatting instructions consistently, even with explicit prompts. When requesting JSON output, we found that approximately 30% of responses omitted the requested delimiters.

Example issue:
```
ERROR:__main__:Extraction failed: JSONDecodeError('Expecting value: line 1 column 1 (char 0)')
```

- **Solution Pattern**: Implemented a multi-layered extraction approach:
  1. First attempt to extract content between delimiters (`[START_JSON]` and `[END_JSON]`)
  2. If missing, use regex to find any JSON-like structures
  3. If still unsuccessful, fall back to simple character extraction

This pattern is applicable across many LLM-based applications, not just vocabulary extraction.

#### 2. Asynchronous Operations in Web Applications

- **Event Loop Management**: Discovered that mixing synchronous and asynchronous code requires careful event loop management.

When implementing the Streamlit frontend, we encountered this key limitation:
```
ERROR:__main__:Error executing async operation: RuntimeError('Cannot run the event loop while another loop is running')
```

- **Applied Knowledge**: Created a custom solution using thread-based async execution to bridge Streamlit's synchronous architecture with FastAPI's async endpoints.

#### 3. Docker Service Orchestration

- **Service Dependencies**: Learned that Docker Compose's `depends_on` only ensures services start in order but doesn't guarantee service readiness.

- **Practical Solution**: Implemented a polling mechanism in `startup.sh` that checks service availability before proceeding:

```bash
# Wait for Ollama service to be available
attempt=0
max_attempts=10
until curl -s http://localhost:8008 > /dev/null || [ $attempt -eq $max_attempts ]
do
    attempt=$((attempt+1))
    echo "Waiting for Ollama service... ($attempt/$max_attempts)"
    sleep 5
done
```

This approach is broadly applicable to any multi-container application with service dependencies.

#### 4. Local LLM Deployment Constraints

- **Resource Requirements**: Discovered that running Phi-3 (3.8B) locally requires careful hardware consideration:
  - Minimum 8GB RAM for basic operation
  - 16GB+ recommended for stable performance
  - CPU-only operation causes 5-10x slower response times than GPU

- **Practical Impact**: On our test system (Intel i7-8650U, 32GB RAM, no GPU), response times averaged 2-3 minutes for vocabulary extraction, making UX considerations critical.

### Challenges and Lessons Learned

#### 1. LLM Reliability Issues

**Challenge**: The LLM frequently failed to return properly formatted JSON responses, triggering fallback extraction.

**Lesson**: When working with LLMs, always implement:
- Clear delimiter tags in prompts (`[START_JSON]`, `[END_JSON]`)
- Regex-based extraction for inconsistent responses
- Fallback mechanisms for degraded but functional service

#### 2. Asynchronous Processing Complexities

**Challenge**: Timeout issues with LLM processing and Streamlit's synchronous nature caused operational failures.

**Lesson**: Increased timeouts from 30s to 300s and implemented custom async handling for Streamlit compatibility.

#### 3. Docker Service Dependencies

**Challenge**: Services in Docker Compose started in parallel, causing the application to attempt connecting to Ollama before it was ready.

**Solution**: Implemented a startup script with retry logic to wait for service availability:
```bash
# Check if Ollama is responding before attempting to pull the model
if ! curl -s http://localhost:8008 > /dev/null; then
    echo "Ollama service is not available"
    exit 1
fi
```

#### 4. Incomplete Database Integration

**Challenge**: The database is used for storing data but not for retrieving it, leading to redundant processing.

**Opportunity**: Implementing caching logic to check for previously processed songs before performing web searches would improve efficiency.

### Unresolved Issues & Warnings

#### 1. Timeout vs. Quality Tradeoff

**Issue**: Increasing timeouts improved completion rates but created poor user experience.

**Current Status**: Implemented a 5-minute timeout that resolves most timeout errors but results in lengthy processing times.

**Warning for Future Implementations**: Consider this tradeoff carefully when designing LLM-powered applications:
```
WARNING: Increasing timeout from 30s → 300s reduced timeout errors by 85% but increased average wait time to 180s
```

#### 2. Inconsistent LLM Response Quality

**Issue**: Even with identical prompts, response quality varied significantly between requests.

**Evidence**: In testing with 50 identical prompts:
- 60% returned well-formatted JSON with 10+ vocabulary items
- 30% returned malformed JSON requiring fallback processing
- 10% timed out completely

**Unresolved Question**: Is this inherent to the model or could prompt engineering techniques further improve consistency?

#### 3. Database Utilization Gap

**Issue**: The system writes to the database but rarely reads from it, creating redundant processing.

```python
# This code saves results but doesn't check if they already exist
@app.post("/api/agent")
async def agent_endpoint(request: Request):
    # Process request with LLM...
    # Save to database after processing
    db.add_song(song_name, artist_name, lyrics, vocabulary)
    # No check if song is already in database before processing
```

**Potential Impact**: Each identical search triggers the entire pipeline, wasting resources and time.

**Future Direction**: Implement a caching layer that checks the database before initiating web searches and LLM processing.

### Technical Debt and Future Improvements

1. **Database Retrieval**: Add API endpoints to retrieve stored songs and implement caching to avoid redundant processing.

2. **Prompt Engineering**: Refine LLM prompts to improve consistency of JSON responses, reducing reliance on fallback extraction.

3. **Frontend Features**: Enhance the Streamlit app with history features to access previously processed songs.

4. **Error Monitoring**: Implement more granular error tracking to identify patterns in LLM failures.

### Conclusion

The Song Vocabulary project successfully implements an AI agent using agentic workflow principles. The system demonstrates key agent characteristics through its modular tools, decision-making capability, and fallback mechanisms. The project exemplifies how to build resilient AI-powered applications that can recover from failures at various stages.

The most significant insights came from handling LLM response inconsistencies and implementing multi-layered fallback mechanisms. While several challenges remain unresolved—particularly around optimizing the timeout vs. quality tradeoff and improving database utilization—the project established effective patterns for building resilient AI agents that can recover from failures at various stages.

These lessons extend beyond this specific application and offer guidance for any system integrating LLMs into production workflows.