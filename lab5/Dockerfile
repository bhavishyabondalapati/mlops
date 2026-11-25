# ---------- Stage 1: train the model and run the tests ----------
FROM python:3.12-slim AS builder
WORKDIR /build

# Install dependencies before copying code, so Docker can reuse this layer
# when only the code changes (much faster rebuilds)
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY src/ src/
COPY tests/ tests/
RUN cd src && python train.py
# If any test fails, the build stops here and no image is produced
RUN python -m pytest -q tests

# ---------- Stage 2: the image that actually runs ----------
FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY --from=builder /build/model/ model/

# Don't run the server as root
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

# Docker checks /health every 30s and marks the container unhealthy if it stops answering
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
