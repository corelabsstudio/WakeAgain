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

RUN mkdir -p /data
VOLUME ["/data"]

EXPOSE 8080
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
