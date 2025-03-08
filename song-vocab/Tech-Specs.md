# Tech Specs

## Business Goal
We want to create a program that will find lyrics on the internet for a target song in Putonghua and produce vocabulary to be imported into our database. The target audience includes language learners, educators, and developers who need structured vocabulary data. The vocabulary should be exportable to a backend server for further processing and integration into various applications.

## Technical Requirements
- FastAPI
- Ollama via the Ollama Python SDK
  - Phi4-mini (3.8B)
- SQLite3 (for database)
- duckduckgo-search-python (for web search)

## API Endpoints

### GetLyrics /api/agent

#### Behavior
This endpoint interacts with our agent, which uses the React framework to search the internet, find multiple possible versions of lyrics, extract the correct lyrics, and format them into vocabulary.

Tools available to the agent include:
- tools/extract_vocabulary.py
- tools/get_page_content.py
- tools/search_web.py
- tools/generate_song_id.py

#### JSON Request Parameters
- `message_request` (str): (required) A string that describes the song and/or artist to get the lyrics from the internet.
- `artist_name` (str): (optional) The name of the artist.

#### JSON Response Parameters
- `lyrics` (str): The lyrics of the song.
- `vocabulary` (list): A list of all the vocabulary words found in the lyrics in a specific JSON format.

### GetVocabulary /api/get_vocabulary
This endpoint takes a text file for a song and returns a list of all the vocabulary words found in the lyrics in a specific JSON format.

### Agent Prompt
The agent prompt is defined in the file `lyrics-agent.md`.

### Decoupled Tools
- `extract_vocabulary.py`: This tool takes a body of text and extracts all the vocabulary into a specific structured JSON output, including the jiantizi, pinyin, and English translation.
- `get_page_content.py`: This tool takes web page content and parses it to extract the target text.
- `search_web.py`: This tool uses DuckDuckGo to search the internet for pages to further crawl.
- `generate_song_id.py`: This tool generates URL-safe strings from artist and title, removes special characters, converts to lowercase, and replaces spaces with hyphens.

### Example Project Structure
```
song-vocab/
├── main.py                     # Main application
├── agent.py                    # Agent
├── database.py                 # Database
├── requirements.txt            # Python dependencies
├── prompts/
│   ├── lyrics-agent.md         # Lyrics agent prompt
│   └── vocabulary-agent.md     # Vocabulary agent prompt
├── tools/
│   ├── extract_vocabulary.py   # Extract vocabulary tool
│   ├── get_page_content.py     # Get page content tool
│   └── search_web.py           # Search web tool
│   └── generate_song_id.py     # Generate song id tool
├── outputs/
├── bin/
│   ├── post/
├── README.md                   # Project overview and documentation
```

## Testing Strategy

### Unit Tests
- **Purpose**: To test individual components and functions in isolation.
- **Scope**: Each function and method in the codebase.
- **Tools**: `unittest` or `pytest`.
- **Examples**:
  - Test the `generate_song_id` function to ensure it correctly formats strings.
  - Test the `extract_vocabulary` function to verify it extracts vocabulary correctly.

### Integration Tests
- **Purpose**: To test the interaction between different components and ensure they work together as expected.
- **Scope**: Interactions between modules, such as API endpoints and database operations.
- **Tools**: `pytest` with fixtures.
- **Examples**:
  - Test the `/api/agent` endpoint to ensure it correctly processes requests and returns the expected JSON response.
  - Test the database interactions to ensure data is correctly stored and retrieved.

### End-to-End Tests
- **Purpose**: To test the entire application flow from start to finish.
- **Scope**: The complete user journey, including API requests and responses.
- **Tools**: `Selenium` or `Cypress` for web-based testing.
- **Examples**:
  - Simulate a user requesting lyrics and verify the correct lyrics and vocabulary are returned.
  - Test the full workflow of extracting vocabulary from a text file and storing it in the database.

### Error Handling Tests
- **Purpose**: To ensure the application handles errors gracefully and provides meaningful error messages.
- **Scope**: All error scenarios, including invalid inputs and unexpected failures.
- **Tools**: `pytest`.
- **Examples**:
  - Test how the application handles invalid URLs or missing parameters.
  - Verify that appropriate error messages are returned for 404 and 500 errors.

### Logging and Debugging
- **Purpose**: To ensure sufficient logging is in place for debugging and monitoring.
- **Scope**: All critical operations and error scenarios.
- **Tools**: Python's `logging` module.
- **Examples**:
  - Verify that all errors are logged with sufficient detail.
  - Ensure that important operations, such as database interactions, are logged.

I have a tech spec for a project that involves creating a FastAPI app, an agent, its prompt, and several tools. I need your help to implement this. Please consider reusing existing libraries and minimizing the number of external libraries to reduce the risk of dependency conflicts. Here are the details: