FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    cron \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN uv pip install --system -e .

COPY docker/crontab /etc/cron.d/quant-scan
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod 0644 /etc/cron.d/quant-scan && chmod +x /entrypoint.sh

RUN mkdir -p /app/data/output /app/data/history /app/data/cache /app/logs

ENV TZ=America/New_York

VOLUME ["/app/data", "/app/logs"]

ENTRYPOINT ["/entrypoint.sh"]
