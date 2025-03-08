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
python -m tests.test_agent

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
python -m tests.test_api

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