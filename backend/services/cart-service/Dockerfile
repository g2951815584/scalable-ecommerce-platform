FROM python:3.12-slim AS builder
WORKDIR /build
RUN python -m venv /opt/venv
COPY libs/common /build/libs/common
COPY services/cart-service /build/service
RUN /opt/venv/bin/pip install --no-cache-dir /build/libs/common /build/service

FROM python:3.12-slim
RUN useradd --create-home --uid 1000 appuser
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /build/service/app /app/app
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
USER appuser
EXPOSE 8003
HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8003/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]