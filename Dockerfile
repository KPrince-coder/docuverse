# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for PyMuPDF and other packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better cache utilization
COPY requirements.txt .

# Create a virtual environment
RUN python -m venv /venv

# Install Python dependencies inside the virtual environment
RUN /venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p data/uploads data/notes cache storage

# Expose Streamlit's default port
EXPOSE 8501

# Set environment variables for Streamlit
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=localhost

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run the application using the virtual environment
ENTRYPOINT ["/venv/bin/streamlit", "run", "app.py", "--server.port=8501", "--server.headless=true"]
