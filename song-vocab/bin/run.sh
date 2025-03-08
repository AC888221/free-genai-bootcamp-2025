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