FROM python:3.12-slim

# Verilator is required for server-side RTL lint (WP-04).
RUN apt-get update \
    && apt-get install -y --no-install-recommends verilator \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv for fast, reproducible dependency installs.
RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
COPY backend/ ./backend/

RUN uv pip install --system --no-cache .

EXPOSE 8000

ENTRYPOINT ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
