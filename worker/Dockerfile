# syntax=docker/dockerfile:1
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
RUN groupadd --system appgroup \
    && useradd --system --gid appgroup --home-dir /app appuser
COPY --from=builder /install /usr/local
COPY worker.py healthcheck.py .
RUN chown -R appuser:appgroup /app
USER appuser
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python healthcheck.py
CMD ["python", "worker.py"]
