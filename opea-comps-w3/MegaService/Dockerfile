FROM python:3.10-slim

WORKDIR /app

# Install curl for healthchecks and system utilities
RUN apt-get update && apt-get install -y curl procps && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .
COPY MegaTalk.py .

# Create log directory
RUN mkdir -p /var/log

EXPOSE 9500 8501

# Create a more robust start script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Start FastAPI server\n\
python server.py --host 0.0.0.0 --port 9500 > /var/log/server.log 2>&1 &\n\
FASTAPI_PID=$!\n\
\n\
# Wait for FastAPI to be ready\n\
echo "Waiting for FastAPI server..."\n\
for i in {1..30}; do\n\
    if curl -s http://localhost:9500/health > /dev/null; then\n\
        echo "FastAPI server is ready!"\n\
        break\n\
    fi\n\
    if [ "$i" = 30 ]; then\n\
        echo "FastAPI server failed to start!"\n\
        exit 1\n\
    fi\n\
    sleep 1\n\
done\n\
\n\
# Start Streamlit\n\
echo "Starting Streamlit server..."\n\
streamlit run MegaTalk.py --server.port=8501 --server.address=0.0.0.0 > /var/log/streamlit.log 2>&1 &\n\
STREAMLIT_PID=$!\n\
\n\
# Monitor both processes\n\
while true; do\n\
    if ! ps -p $FASTAPI_PID > /dev/null || ! ps -p $STREAMLIT_PID > /dev/null; then\n\
        echo "One of the services has died!"\n\
        exit 1\n\
    fi\n\
    sleep 5\n\
done\n\
' > /app/start.sh

RUN chmod +x /app/start.sh

# Simplified health check that only checks the FastAPI service
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9500/health || exit 1

CMD ["/app/start.sh"] 