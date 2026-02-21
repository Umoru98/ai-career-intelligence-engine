FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --timeout 300 --retries 10 -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Pre-download sentence-transformers model (offline-first)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy application code
COPY . .

# Ensure start.sh is executable
USER root
RUN chmod +x /app/start.sh
USER appuser

# Create upload directory
RUN mkdir -p /data/uploads

# Non-root user for security (managed in previous step)
# USER appuser

EXPOSE 8000

CMD ["/bin/bash", "start.sh"]

