FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Make scripts executable
RUN chmod +x music_server.py mcp_pipe.py

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV ADAPTER_URL=http://xiaozhi-adapter:5005

# Expose port (optional, for monitoring)
EXPOSE 5006

# Production stage
FROM base AS production

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=30s \
    CMD pgrep -f "python3 mcp_pipe.py" || exit 1

# Default command
CMD ["python3", "mcp_pipe.py"]

# Development stage
FROM base AS development

# Development command with unbuffered output
CMD ["python3", "-u", "mcp_pipe.py"]