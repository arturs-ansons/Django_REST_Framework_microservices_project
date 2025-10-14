FROM python:3.11-slim

WORKDIR /app

# Install build dependencies for mysqlclient
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir uvicorn  # add uvicorn if using ASGI

COPY . .

EXPOSE 8000

CMD ["uvicorn", "shipping_service.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
