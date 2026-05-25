FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -e .

COPY src/ms3/ /app/src/ms3/
COPY web/dist/ /app/web/dist/

RUN mkdir -p /data/workspaces

EXPOSE 8080

CMD ["uvicorn", "src.ms3.api.app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
