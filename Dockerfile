# Use official Python base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install required build tools BEFORE installing project dependencies
RUN pip install --upgrade pip setuptools wheel

# Copy project files
COPY . .

# Install project dependencies (single command — recommended for production)
RUN pip install --no-cache-dir -r requirements.txt

# Expose Django default port
EXPOSE 8000

# Start Django dev server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

