FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8084

ENV NAME TubeQuiz
ENV PYTHONUNBUFFERED=1

CMD ["streamlit", "run", "frontend/TubeQuiz.py", "--server.port=8084", "--server.address=0.0.0.0"]