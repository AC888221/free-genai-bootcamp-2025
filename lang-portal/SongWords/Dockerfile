FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /root/.songwords/logs

EXPOSE 8083

ENV NAME SongWords
ENV PYTHONUNBUFFERED=1

CMD ["streamlit", "run", "SongWords.py", "--server.port=8083", "--server.address=0.0.0.0"]