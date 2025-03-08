#!/bin/bash

# Create the main directories
mkdir -p song-vocab/prompts
mkdir -p song-vocab/tools
mkdir -p song-vocab/outputs
mkdir -p song-vocab/bin/post

# Create empty __init__.py files for Python packages
touch song-vocab/__init__.py
touch song-vocab/tools/__init__.py

# Create a README.md file
cat > song-vocab/README.md << 'EOF'
# Song Vocabulary Extractor

A FastAPI application that finds lyrics for songs in Putonghua (Mandarin Chinese) and extracts vocabulary for language learners.

## Business Goal
This program finds lyrics on the internet for a target song in Putonghua and produces vocabulary to be imported into our database. The target audience includes language learners, educators, and developers who need structured vocabulary data.

## Features
- Search for song lyrics by title and artist
- Extract vocabulary from lyrics, including simplified characters, pinyin, and English translations
- Store lyrics and vocabulary in a SQLite database
- API endpoints for retrieving lyrics and vocabulary

## Technical Stack
- FastAPI
- Ollama with Phi4-mini (3.8B)
- SQLite3
- DuckDuckGo Search Python

## Getting Started

### Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Make sure Ollama is installed and the Phi4-mini model is available

### Running the Application
```bash
cd song-vocab
python main.py
```

The API will be available at http://localhost:8000

### API Endpoints
- `GET /`: Welcome message
- `POST /api/agent`: Get lyrics and vocabulary for a song
- `POST /api/get_vocabulary`: Extract vocabulary from provided text

## License
[MIT License](LICENSE)
EOF

echo "Project structure created successfully"

song-vocab/
├── __init__.py
├── .gitignore
├── main.py
├── agent.py
├── database.py
├── init_db.py
├── requirements.txt
├── README.md
├── prompts/
│   ├── __init__.py
│   ├── lyrics-agent.md
│   └── vocabulary-agent.md
├── tools/
│   ├── __init__.py
│   ├── search_web.py
│   ├── get_page_content.py
│   ├── extract_vocabulary.py
│   └── generate_song_id.py
├── outputs/
│   └── .gitkeep
├── bin/
│   ├── run.sh
│   ├── run_tests.sh
│   └── post/
│       └── .gitkeep
└── tests/
    ├── __init__.py
    ├── test_agent.py
    └── test_api.py


Implementation Summary
I've created a complete implementation of the song vocabulary extraction system according to your tech specs. The solution includes:

FastAPI Application (main.py)

Two API endpoints: /api/agent and /api/get_vocabulary
Structured request and response models
Database integration


LyricsAgent (agent.py)

Uses Ollama with the Phi4-mini model
Implements a React-like approach for multi-step reasoning
Parses and executes tool calls
Handles conversation history


Database Layer (database.py)

SQLite3 implementation with two tables: songs and vocabulary
Methods for saving and retrieving songs and vocabulary


Tools Implementation

search_web.py: Uses DuckDuckGo to search for lyrics
get_page_content.py: Fetches and cleans web page content
extract_vocabulary.py: Uses Ollama to extract vocabulary from text
generate_song_id.py: Creates URL-safe IDs for songs


Prompts

lyrics-agent.md: Detailed instructions for the agent


Project Setup

Let me continue with the implementation by adding some testing code and filling out the remaining pieces:



# Chinese Vocabulary Extraction Agent

You are an agent designed to extract vocabulary from Chinese (Putonghua) text for language learners.

## Your Task
Your goal is to analyze Chinese text and extract vocabulary items that would be valuable for language learners. You should:

1. Identify unique Chinese words and characters
2. Determine the simplified form (jiantizi) of each word
3. Provide the pinyin romanization with tone marks
4. Translate each word into English

## Process
1. Analyze the provided text to identify vocabulary items
2. Focus on words that would be valuable for language learners
3. Ignore common words like pronouns, conjunctions, and particles unless they're important
4. Provide complete information for each vocabulary item
5. Limit to a maximum of 30 vocabulary items

## Output Format
Your output should be a list of vocabulary items in this format:

```json
[
  {
    "word": "中文",
    "jiantizi": "中文",
    "pinyin": "zhōng wén",
    "english": "Chinese language"
  },
  {
    "word": "学习",
    "jiantizi": "学习",
    "pinyin": "xué xí",
    "english": "to study, to learn"
  }
]
```

## Rules
1. Include a diverse range of vocabulary items, including nouns, verbs, adjectives, and useful expressions
2. Prioritize words that appear frequently or are important to understanding the text
3. Include both individual characters and multi-character words where appropriate
4. Provide accurate pinyin with tone marks
5. Give clear and concise English translations
6. If a word has multiple meanings, prioritize the meaning that fits the context of the provided text


```python
import json
import os
import sys
from agent import LyricsAgent

def test_agent():
    """Test the LyricsAgent with a sample song."""
    print("Testing LyricsAgent...")
    
    # Create agent
    agent = LyricsAgent()
    
    # Test with a well-known Chinese song
    song_request = "月亮代表我的心"
    artist_name = "邓丽君"  # Teresa Teng
    
    print(f"Searching for: {song_request} by {artist_name}")
    
    # Run the agent
    try:
        result = agent.run(song_request, artist_name)
        
        # Print the results
        print("\n=== LYRICS ===")
        print(result["lyrics"][:200] + "..." if len(result["lyrics"]) > 200 else result["lyrics"])
        
        print("\n=== VOCABULARY SAMPLE ===")
        for i, vocab in enumerate(result["vocabulary"][:5]):
            print(f"{i+1}. {vocab['word']} ({vocab['jiantizi']}) - {vocab['pinyin']} - {vocab['english']}")
        
        print(f"\nTotal vocabulary items: {len(result['vocabulary'])}")
        
        # Save results to a file
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, f"{song_request}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\nResults saved to {output_file}")
        return True
    except Exception as e:
        print(f"Error testing agent: {str(e)}")
        return False

def test_vocabulary_extraction():
    """Test vocabulary extraction with a sample text."""
    print("\nTesting vocabulary extraction...")
    
    # Sample Chinese text
    sample_text = """
    月亮代表我的心
    你问我爱你有多深
    我爱你有几分
    你去想一想
    你去看一看
    月亮代表我的心
    """
    
    # Create agent
    agent = LyricsAgent()
    
    try:
        # Extract vocabulary
        vocabulary = agent.extract_vocabulary(sample_text)
        
        # Print results
        print("\n=== EXTRACTED VOCABULARY ===")
        for i, vocab in enumerate(vocabulary):
            print(f"{i+1}. {vocab['word']} ({vocab['jiantizi']}) - {vocab['pinyin']} - {vocab['english']}")
        
        print(f"\nTotal vocabulary items: {len(vocabulary)}")
        return True
    except Exception as e:
        print(f"Error testing vocabulary extraction: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_agent() and test_vocabulary_extraction()
    sys.exit(0 if success else 1)

```

```python
import requests
import json
import time
import sys

def test_api_endpoints():
    """Test the API endpoints."""
    base_url = "http://localhost:8000"
    
    print("Testing API endpoints...")
    
    # Wait for the server to start
    server_ready = False
    max_retries = 5
    retries = 0
    
    while not server_ready and retries < max_retries:
        try:
            # Test the root endpoint
            response = requests.get(f"{base_url}/")
            if response.status_code == 200:
                server_ready = True
                print("Server is running")
            else:
                print(f"Server not ready yet (status code: {response.status_code}), retrying...")
                time.sleep(2)
                retries += 1
        except requests.exceptions.ConnectionError:
            print("Server not ready yet, retrying...")
            time.sleep(2)
            retries += 1
    
    if not server_ready:
        print("Server did not start in time, exiting")
        return False
    
    # Test the agent endpoint
    try:
        print("\nTesting /api/agent endpoint...")
        
        payload = {
            "message_request": "月亮代表我的心",
            "artist_name": "邓丽君"
        }
        
        response = requests.post(f"{base_url}/api/agent", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("Success! Sample of lyrics:")
            print(result["lyrics"][:200] + "..." if len(result["lyrics"]) > 200 else result["lyrics"])
            print(f"Number of vocabulary items: {len(result['vocabulary'])}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Error testing agent endpoint: {str(e)}")
        return False
    
    # Test the vocabulary endpoint
    try:
        print("\nTesting /api/get_vocabulary endpoint...")
        
        payload = {
            "text": "月亮代表我的心\n你问我爱你有多深\n我爱你有几分"
        }
        
        response = requests.post(f"{base_url}/api/get_vocabulary", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("Success! Sample of vocabulary:")
            for i, vocab in enumerate(result["vocabulary"][:3]):
                print(f"{i+1}. {vocab['word']} - {vocab['pinyin']} - {vocab['english']}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Error testing vocabulary endpoint: {str(e)}")
        return False
    
    print("\nAll API tests completed successfully")
    return True

if __name__ == "__main__":
    success = test_api_endpoints()
    sys.exit(0 if success else 1)

```

```python
# Import all tools for easier access
from .search_web import search_web
from .get_page_content import get_page_content
from .extract_vocabulary import extract_vocabulary
from .generate_song_id import generate_song_id

__all__ = [
    'search_web',
    'get_page_content',
    'extract_vocabulary',
    'generate_song_id'
]

```

```bash
#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Song Vocabulary Application...${NC}"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}Ollama is not installed. Please install Ollama first.${NC}"
    echo "Visit https://ollama.ai for installation instructions."
    exit 1
fi

# Check if phi4-mini model is available
if ! ollama list | grep -q "phi4-mini"; then
    echo -e "${BLUE}Downloading phi4-mini model...${NC}"
    ollama pull phi4-mini
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Check and install requirements
if [ -f "requirements.txt" ]; then
    echo -e "${BLUE}Installing requirements...${NC}"
    pip install -r requirements.txt
fi

# Run the API server
echo -e "${GREEN}Starting API server...${NC}"
python main.py

```

```bash
#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Running Song Vocabulary Application Tests...${NC}"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Run the agent tests
echo -e "${BLUE}Running agent tests...${NC}"
python test_agent.py

# Check test result
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Agent tests passed successfully!${NC}"
else
    echo -e "${RED}Agent tests failed.${NC}"
    exit 1
fi

# Start the API server in the background
echo -e "${BLUE}Starting API server for tests...${NC}"
python main.py &
SERVER_PID=$!

# Give the server some time to start
echo -e "${BLUE}Waiting for server to start...${NC}"
sleep 5

# Run the API tests
echo -e "${BLUE}Running API tests...${NC}"
python test_api.py

# Check API test result
API_RESULT=$?

# Kill the server
echo -e "${BLUE}Stopping the server...${NC}"
kill $SERVER_PID

# Final result
if [ $API_RESULT -eq 0 ]; then
    echo -e "${GREEN}All tests passed successfully!${NC}"
    exit 0
else
    echo -e "${RED}API tests failed.${NC}"
    exit 1
fi

```

```python
from database import Database

def initialize_database():
    """Initialize the database and create tables."""
    print("Initializing database...")
    db = Database()
    db.create_tables()
    print("Database initialized successfully.")

if __name__ == "__main__":
    initialize_database()

```

## Project Documentation

Here's a comprehensive overview of what I've built:

### Core Components

1. **FastAPI Application (main.py)**
   - Provides two main API endpoints: `/api/agent` and `/api/get_vocabulary`
   - Uses Pydantic models for request/response validation
   - Initializes the database on startup

2. **LyricsAgent (agent.py)**
   - Implements a ReAct-style agent using Ollama and Phi4-mini
   - Manages conversation flow and tool calls
   - Parses responses to extract final results

3. **Database (database.py)**
   - SQLite3-based storage for songs and vocabulary
   - Handles song storage and retrieval
   - Uses foreign keys to relate vocabulary to songs

4. **Tools**
   - Web search (using DuckDuckGo)
   - Page content extraction
   - Vocabulary extraction
   - Song ID generation

### Getting Started

To run the application:

1. Make sure Ollama is installed on your system
2. Install the requirements: `pip install -r requirements.txt`
3. Run the application: `python main.py` or `./run.sh`
4. The API will be available at http://localhost:8000

### API Endpoints

1. **GET /**
   - Simple welcome message

2. **POST /api/agent**
   - Request body:
     ```json
     {
       "message_request": "月亮代表我的心",
       "artist_name": "邓丽君"
     }
     ```
   - Response:
     ```json
     {
       "lyrics": "月亮代表我的心...",
       "vocabulary": [
         {
           "word": "月亮",
           "jiantizi": "月亮",
           "pinyin": "yuè liàng",
           "english": "moon"
         },
         ...
       ]
     }
     ```

3. **POST /api/get_vocabulary**
   - Request body:
     ```json
     {
       "text": "Chinese text to extract vocabulary from"
     }
     ```
   - Response:
     ```json
     {
       "vocabulary": [
         {
           "word": "...",
           "jiantizi": "...",
           "pinyin": "...",
           "english": "..."
         },
         ...
       ]
     }
     ```

### Testing

I've included two testing scripts:

1. **test_agent.py** - Tests the agent directly with a well-known Chinese song
2. **test_api.py** - Tests the API endpoints

To run the tests: `./run_tests.sh`

### Next Steps

1. **Error Handling Enhancement**: Add more robust error handling and retry mechanisms for web searches and API calls
2. **Performance Optimization**: Implement caching for previously searched songs
3. **User Interface**: Consider adding a simple web UI for easier interaction
4. **Expanded Models**: Support for additional language models beyond Phi4-mini
5. **Multiple Languages**: Extend to support other languages beyond Putonghua


13:30 vid: just use duckduckgo, in genai essentials Andrew uses SerpApi, need account.