FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .
COPY MegaTalk.py .

EXPOSE 9500 8501

# Create a script to run both FastAPI and Streamlit
RUN echo '#!/bin/bash\npython server.py &\nstreamlit run MegaTalk.py --server.port=8501 --server.address=0.0.0.0' > /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"] 