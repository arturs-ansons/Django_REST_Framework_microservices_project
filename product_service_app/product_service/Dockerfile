FROM python:3.11-slim

WORKDIR /app

# Install build dependencies for mysqlclient and system tools
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir uvicorn  # needed for ASGI

# Copy app source code
COPY . .

# Expose API port
EXPOSE 8000

# Default command: run the API
CMD ["uvicorn", "product_service.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
