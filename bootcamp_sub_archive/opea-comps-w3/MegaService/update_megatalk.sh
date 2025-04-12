#!/bin/bash

# Get the container ID of the megaservice
CONTAINER_ID=$(docker ps | grep opea-megaservice | awk '{print $1}')

if [ -z "$CONTAINER_ID" ]; then
  echo "Megaservice container not found!"
  exit 1
fi

# Copy your local MegaTalk.py into the container
echo "Copying MegaTalk.py to container..."
docker cp /mnt/c/Users/Andrew/Documents/freegenai/opea-comps-w3/MegaService/MegaTalk.py $CONTAINER_ID:/app/MegaTalk.py

# Restart Streamlit in the container
echo "Restarting Streamlit..."
docker exec $CONTAINER_ID pkill -f streamlit
docker exec -d $CONTAINER_ID streamlit run /app/MegaTalk.py

echo "Done! Refresh your browser to see changes."
