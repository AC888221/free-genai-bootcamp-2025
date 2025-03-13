FROM ollama/ollama

RUN apt-get update && apt-get install -y curl

COPY startup.sh /startup.sh
RUN chmod +x /startup.sh

ENTRYPOINT ["/startup.sh"]