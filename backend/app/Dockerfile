FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY backend/app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app .
RUN mkdir -p /app/assets
COPY logo.jpg /app/assets/logo.jpg

RUN mkdir -p /app/uploads

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["sh", "scripts/start-backend.sh"]
