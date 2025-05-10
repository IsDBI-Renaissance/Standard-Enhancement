FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set environment variables
ENV PORT=8000
ENV DEFAULT_QUALITY_SCORE=60
ENV MAX_RETRIES=5

EXPOSE 8000

CMD ["python", "server.py"]
