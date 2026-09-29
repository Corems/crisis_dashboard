FROM python:3.12-slim

WORKDIR /app

ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# generate gRPC code from proto files
RUN python -m grpc_tools.protoc \
    -I./proto \
    --python_out=./app/grpc \
    --grpc_python_out=./app/grpc \
    proto/crisis.proto

CMD ["python", "-m", "app.main"]
