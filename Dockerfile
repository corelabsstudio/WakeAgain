FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APP_ENV=production MATCH_DATA_DIR=/data/matching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py ops.py portfolio_import.py service_features.py social_auth.py alimtalk.py collaboration.py price_sources.json ./
COPY public ./public
RUN mkdir -p /data/matching
EXPOSE 8080
CMD ["sh", "-c", "exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}"]
