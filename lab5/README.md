# Lab 5: Packaging the model API with Docker

Based on `Docker_Labs/Lab1`. The course lab builds an image that trains a random forest on the Iris dataset and saves it to a file inside the container. Once training finishes, the container exits, so the model is never used and is gone with the container.

I used Docker to package something that keeps running: the claims risk-tier API from Lab 4 (FastAPI + scikit-learn). The image trains the model, tests it, and then serves it on port 8000 inside the container (8001 on my Mac). Anyone with Docker can run the same API with one command, without installing Python or any packages.

## What I changed from the course lab

**The container serves the model instead of exiting.** The image's start command runs the FastAPI server (`uvicorn`), so the trained model is actually used.

**Two-stage build.** The first stage installs pytest, trains the model and runs the API tests. The second stage starts from a clean image and copies in only the code and the trained model file, so test tools don't end up in the final image.

**Tests run during the build.** If any test fails, `docker build` stops and no image is created, so a broken API can't be shipped.

**Smaller base image.** `python:3.12-slim` instead of the full `python:3.10` image, which is several hundred MB bigger.

**Faster rebuilds.** Requirements are copied and installed before the code. Docker caches each step, so changing only the code reuses the installed packages instead of reinstalling everything.

**Pinned versions.** The model is trained in one stage and loaded in another. scikit-learn has to be the exact same version in both, or the saved model might not load, so every package version is fixed in `requirements.txt`.

**Health check.** Docker calls `/health` every 30 seconds. `docker ps` shows the container as `healthy`, or `unhealthy` if the API stops answering.

**Not running as root.** The server runs as a normal user (`appuser`), so a bug in the app can't do as much damage inside the container.

**`.dockerignore` and `docker-compose.yml`.** The ignore file keeps virtual environments, old model files and results out of the image. The compose file lets you start everything with `docker compose up`.

## How to run

Docker Desktop needs to be running. Then:

```bash
cd lab5
bash run_lab.sh
```

This builds the image, starts the container, and sends a few test requests. The responses are saved to `results/smoke_test.txt`. Open http://127.0.0.1:8001/docs to try the API in the browser.

Useful commands:

```bash
docker ps                          # see the container and its health status
docker logs claims-risk-api        # see the server's log
docker stop claims-risk-api        # stop it
docker compose up --build          # alternative way to build and start
```

## Files

```
lab5/
├── Dockerfile             # two-stage build: train + test, then serve
├── docker-compose.yml
├── .dockerignore
├── requirements.txt       # what the running API needs (pinned)
├── requirements-dev.txt   # plus pytest and httpx, for the build stage only
├── src/                   # API and training code (from Lab 4)
├── tests/test_api.py      # runs inside the build
├── results/smoke_test.txt # output from my run
└── run_lab.sh
```

## Results

The output from my run (image size, `/health`, a prediction, and a rejected bad request) is in `results/smoke_test.txt`.

## Problems I ran into

**Port conflict.** On the first run, the image built and the tests passed, but the test requests got the wrong answers: `/health` returned `{"status":"ok","version":"0.1.0"}` and `/predict` returned 404. Another app on my Mac was already using port 8000, so my requests were going to it instead of the container. I mapped the container to port 8001 on my Mac (`-p 8001:8000`); inside the container the API still runs on 8000.

**Caching in practice.** The first build took about 30 seconds, mostly installing packages. After changing only the port in `run_lab.sh`, the rebuild took 0.4 seconds because every step came from Docker's cache. The final image is 740 MB, mostly scikit-learn, pandas, NumPy and SciPy.
