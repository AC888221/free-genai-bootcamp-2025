# Agents and Agentic Workflow: Vocabulary Extraction

[Jump to Bootcamp Week 3: Agents and Agentic Workflow Implementation Report](#bootcamp-week-3-agents-and-agentic-workflow-implementation-report)

## Song Vocabulary Extractor

A FastAPI and Streamlit application that finds lyrics for songs in Putonghua (Mandarin Chinese) and extracts vocabulary for language learners. For a user-friendly overview of features and screenshots, see our [Showcase](Showcase_song-vocab.md).

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
├── README.md          # Technical documentation
├── Showcase_song-vocab.md  # User-friendly feature showcase
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
- **Database**: Uses SQLite for storing processed songs and vocabulary items
- **Streamlit Frontend**: Offers a user-friendly interface for searching songs and extracting vocabulary

### Key Technical Implementations

#### 1. Agentic Workflow Design

The core of the system is the `LyricsAgent` class that orchestrates a workflow using specialized tools:
```
1. Input Processing: Initial handling of user input
2. Web Search: Retrieving relevant song lyrics
3. Content Retrieval: Fetching the actual lyrics
4. LLM Processing: Extracting vocabulary using the LLM
5. Result Formatting: Preparing the output for the user
```

This demonstrates agency through:
- Chaining multiple tools to accomplish complex tasks
- Making decisions about which tools to use based on the current state
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

Implemented asynchronous HTTP requests using `httpx.AsyncClient` for efficient I/O operations, improving performance and responsiveness:
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

## Challenges, Lessons Learned, and Unresolved Issues

### 1. Language Model Response Handling

LLMs occasionally fail to follow formatting instructions consistently due to their probabilistic nature and the complexity of natural language processing. A multi-layered extraction approach was adopted:
- Initially, content is extracted between delimiters (`[START_JSON]` and `[END_JSON]`).
- If missing, regex is used to find any JSON-like structures.
- If still unsuccessful, a fallback to simple character extraction is employed.

### 2. Asynchronous Operations in Web Applications

Event loop management was crucial for maintaining application stability, especially when mixing synchronous and asynchronous code. A custom solution using thread-based async execution was implemented to bridge Streamlit's synchronous architecture with FastAPI's async endpoints.

### 3. LLM Reliability and Response Quality

To improve LLM response consistency, refined prompt engineering techniques were considered, such as clearer instructions and examples. Implementations included:
- Clear delimiter tags in prompts (`[START_JSON]`, `[END_JSON]`).
- Regex-based extraction for inconsistent responses.
- Fallback mechanisms for degraded but functional service.

### 4. Asynchronous Processing Complexities

Trade-offs between timeout duration and user experience were addressed. Increasing timeouts from 30s to 300s reduced timeout errors by 85% but increased average wait time to 180s. Strategies like optimizing prompt efficiency or parallel processing were considered to mitigate long wait times.

### 5. Docker Service Orchestration

Docker-compose was modified to automate Ollama's model pull. However, docker-compose starts services in order but doesn't ensure readiness, leading to premature connection attempts to Ollama. To address this, a polling mechanism was added in startup.sh (Commit 516fefe) to check service availability, but it failed as the service wasn't ready and the container wasn't fully initialized. Despite this failure, further investigateion may enable integration of Ollama's model pull into the docker initialization process.

### 6. Database Utilization Gap

One current challenge is that the database is used only for storing data, not retrieving it, resulting in redundant processing. An opportunity to improve efficiency is by implementing caching logic to check for previously processed songs before performing web searches. Also, integrating the app with the Lang-portal database could provide a more seamless learning experience.

### 7. Local LLM Deployment Constraints

The system resources include an Intel(R) Core(TM) i7-8650U CPU @ 1.90GHz 2.11 GHz with 32.0 GB (31.4 GB usable) and only an integrated GPU. Recommendations for optimizing hardware resources included:
- Ensuring sufficient RAM (16GB+ recommended for stable performance).
- Considering external GPU options for faster processing.
- Optimizing code to reduce computational load.

## Technical Debt and Future Improvements

1. **Database Retrieval**: Develop API endpoints to retrieve stored songs and implement caching mechanisms to minimize redundant processing.

2. **Prompt Engineering**: Enhance LLM prompts to improve the consistency of JSON responses, thereby reducing the dependency on fallback extraction methods.

3. **Iterative Agentive Workflow**: Establish a process where the agent iteratively refines the JSON response until it meets acceptance criteria or, after a predefined number of attempts, defaults to the fallback mechanism. This will improve the agent's autonomous capabilities.

4. **Frontend Features**: Upgrade the Streamlit application to include history features, allowing users to access previously processed songs.

5. **Error Monitoring**: Implement detailed error tracking to identify and analyze patterns in LLM failures, facilitating more effective troubleshooting and improvements.

## Conclusion

The Song Vocabulary project successfully implements an AI agent using agentic workflow principles. The system demonstrates key agent characteristics through its modular tools, decision-making capability, and fallback mechanisms. The project illustrates how to build resilient AI-powered applications capable of recovering from failures at various stages.

Significant insights were gained from handling LLM response inconsistencies and implementing multi-layered fallback mechanisms. While several challenges remain unresolved—particularly around optimizing the timeout vs. quality tradeoff and improving database utilization—the project established effective patterns for building resilient AI agents that can recover from failures at various stages.

These lessons extend beyond this specific application and offer guidance for any system integrating LLMs into production workflows.