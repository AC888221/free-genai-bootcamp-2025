FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /root/.megatalk/logs
RUN mkdir -p /app/audio

EXPOSE 8082

ENV NAME MegaTalk
ENV PYTHONUNBUFFERED=1

CMD ["streamlit", "run", "MegaTalk.py", "--server.port=8082", "--server.address=0.0.0.0"]