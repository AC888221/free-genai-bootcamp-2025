FROM python:3.10-slim

WORKDIR /app

# Install basic utilities
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY MegaTalk.py .

# Create log directory
RUN mkdir -p /var/log

EXPOSE 8082

# Simplified start command for Streamlit only
CMD ["streamlit", "run", "MegaTalk.py", "--server.port=8082", "--server.address=0.0.0.0"] 