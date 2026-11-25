#!/usr/bin/env bash
# Builds the image, starts the container, and checks the API answers.
#   bash run_lab.sh
set -e
cd "$(dirname "$0")"
mkdir -p results
IMAGE=claims-risk-api:1.0
NAME=claims-risk-api
BODY='{"avg_age": 58, "pct_female": 0.6, "members": 300, "chronic_rate": 0.3, "plan": "gold", "region": "northeast"}'

echo "== 1. Building the image (trains the model and runs the tests inside Docker) =="
docker build -t "$IMAGE" .

echo "== 2. Starting the container =="
docker rm -f "$NAME" >/dev/null 2>&1 || true
docker run -d --name "$NAME" -p 8001:8000 "$IMAGE"

echo "Waiting for the API to start..."
for i in $(seq 1 30); do
  curl -s http://127.0.0.1:8001/health >/dev/null && break
  sleep 1
done

echo "== 3. Checking the API =="
{
  echo "Image: $(docker images "$IMAGE" --format '{{.Repository}}:{{.Tag}}  size {{.Size}}')"
  echo
  echo "GET /health"
  curl -s http://127.0.0.1:8001/health; echo
  echo
  echo "POST /predict (high-risk example group)"
  curl -s -X POST http://127.0.0.1:8001/predict -H "Content-Type: application/json" -d "$BODY"; echo
  echo
  echo "POST /predict with avg_age=150 (should be rejected with 422)"
  curl -s -o /dev/null -w "status %{http_code}\n" -X POST http://127.0.0.1:8001/predict \
    -H "Content-Type: application/json" -d "${BODY/58/150}"
} | tee results/smoke_test.txt

echo
echo "== Done! The API is running in Docker. =="
echo "Docs:  http://127.0.0.1:8001/docs"
echo "Stop:  docker stop $NAME"
