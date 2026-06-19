FROM python:3.12-slim

# Install system dependencies (added procps for system/process handling tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    cron \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# Copy project configuration and source code
COPY pyproject.toml README.md ./
COPY src ./src

# Install project with dev and visualization extras for local Linux & Dev Container consistency
RUN uv pip install --system -e .[dev,viz]

# Setup cron and entrypoint scripts
COPY docker/crontab /etc/cron.d/quant-scan
COPY docker/entrypoint.sh /entrypoint.sh

# Fix permission and enforce a trailing blank newline (required by cron daemon)
RUN chmod 0644 /etc/cron.d/quant-scan && \
    echo "" >> /etc/cron.d/quant-scan && \
    chmod +x /entrypoint.sh

# Create required directories for application data and logs
RUN mkdir -p /app/data/output /app/data/history /app/data/cache /app/logs

# Set default Timezone to Eastern Time
ENV TZ=America/New_York

VOLUME ["/app/data", "/app/logs"]

# Explicitly guarantee root execution context so cron daemon starts flawlessly
USER root

ENTRYPOINT ["/entrypoint.sh"]