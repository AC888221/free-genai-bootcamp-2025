#!/bin/sh
ollama serve &

# Maximum retries before attempting model pull
MAX_WAIT_ATTEMPTS=5
WAIT_COUNT=0

# Wait for the service to be available, but don't wait forever
while [ "$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8008)" != "200" ]; do
  echo "Waiting for Ollama service to be available..."
  sleep 2
  WAIT_COUNT=$((WAIT_COUNT + 1))

  # If we waited MAX_WAIT_ATTEMPTS times, try pulling anyway
  if [ "$WAIT_COUNT" -ge "$MAX_WAIT_ATTEMPTS" ]; then
    echo "Service might be up but unresponsive, trying model pull..."
    break
  fi
done

# Reset retry counter for pull attempts
PULL_SUCCESS=1
PULL_RETRIES=0
MAX_PULL_RETRIES=5

# Try pulling the model up to MAX_PULL_RETRIES times
while [ "$PULL_SUCCESS" -ne 0 ] && [ "$PULL_RETRIES" -lt "$MAX_PULL_RETRIES" ]; do
  echo "Attempting to pull model: ${LLM_MODEL_ID} (Attempt $((PULL_RETRIES + 1)))..."
  curl -s -o /dev/null -X POST http://localhost:8008/api/pull -d "{\"model\": \"${LLM_MODEL_ID}\"}"
  
  # Check if model pull succeeded
  if [ $? -eq 0 ]; then
    PULL_SUCCESS=0
    echo "Model pull successful!"
    break
  fi

  echo "Model pull failed, retrying in 5 seconds..."
  sleep 5
  PULL_RETRIES=$((PULL_RETRIES + 1))
done

# Final check
if [ "$PULL_SUCCESS" -ne 0 ]; then
  echo "Failed to pull model after $MAX_PULL_RETRIES attempts. Exiting."
  exit 1
fi