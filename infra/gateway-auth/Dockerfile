FROM python:3.12-slim

RUN useradd --create-home --uid 1000 appuser
WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
USER appuser
EXPOSE 9000
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]