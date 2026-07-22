FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .
COPY wakeagain ./wakeagain
COPY public ./public
# Optional: bake non-secret defaults only; secrets via Railway Variables
ENV AUCTION_SCHEDULER=1
ENV EMAIL_DEV_MODE=0
ENV EMAIL_CODE_FALLBACK=0

RUN mkdir -p /data
# Note: Railway rejects Dockerfile VOLUME — use dashboard Volume mount on /data if needed

EXPOSE 8080
# Railway injects PORT; local default 8080
# Railway sets PORT; shell form so variable expands (exec form would not)
CMD sh -c "exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}"
