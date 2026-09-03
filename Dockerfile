FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the complete backend first
COPY backend /app/backend

# Install backend dependencies
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy the remaining project files
COPY . /app

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]