FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-eng \
    ffmpeg \
    zlib1g-dev \
    libjpeg-dev \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8081

ENV NAME WriteLab
ENV PYTHONUNBUFFERED=1

CMD ["streamlit", "run", "WriteLab.py", "--server.port=8081", "--server.address=0.0.0.0"]