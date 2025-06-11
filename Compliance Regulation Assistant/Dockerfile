# Use official Python base image
FROM python:3.10-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy app code
COPY ./app ./app

# Copy the .env file
COPY .env .env

# Set environment variable for .env path (optional)
ENV ENV_PATH=/app/.env

# Default command to run the app from correct location
CMD ["python", "app/main.py"]
