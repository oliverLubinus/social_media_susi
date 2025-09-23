FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY susi/ ./susi/
COPY token_result.json ./
COPY token_cache.bin ./
COPY gmail_token.json ./
COPY config.yaml ./
COPY logs/ ./logs/
COPY client_secret.json ./
CMD ["python", "-m", "susi.main"]
