FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy app code
COPY . /app

# Default entrypoint runs the sandbox runner; pass --job-id when running
ENTRYPOINT ["python", "-m", "backend.app.sandbox_runner"]
