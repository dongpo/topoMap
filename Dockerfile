FROM python:3.11-slim

WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends gdal-bin \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY data ./data
COPY benchmark ./benchmark
COPY schemas ./schemas
RUN pip install --no-cache-dir .

EXPOSE 8000
CMD ["nma", "serve", "--host", "0.0.0.0", "--port", "8000"]
