# starter-app

A small hello-world web application with a stateful backend, packaged with
Docker and Docker Compose.

This repository is intentionally minimal but **shaped like a real-world
project** so it is a useful **starting point for a Kubernetes support
training capstone**. A support team takes this Docker Compose stack and
converts it into Kubernetes objects — a Deployment, a Service, a ConfigMap,
a Secret, and a StatefulSet with persistent storage.

It deliberately stops at the **container / Compose stage** — there are no
Kubernetes manifests, Helm charts, or deployment YAML in this repo. Adding
those is the training exercise.

## Architecture

```
            +-------------------+         +------------------------+
  client -> |  web (Flask app)  |  -->    |  redis (visit counter) |
            |  stateless        |         |  stateful + volume     |
            +-------------------+         +------------------------+
                    |                               |
              app.config.env                    redis-data
              + .env (secret)                  (persistent volume)
```

- **web** — a stateless Flask app served by gunicorn. Later: a Deployment + Service.
- **redis** — a stateful key/value store that holds a visit counter on a
  persistent volume. Later: a StatefulSet + PersistentVolumeClaim.

## What it is

A small [Flask](https://flask.palletsprojects.com/) app served by
[gunicorn](https://gunicorn.org/), backed by [Redis](https://redis.io/).
There is no authentication, no real database, no queues, and no background
jobs — just three routes, a visit counter, and a clean split between
configuration and secrets.

## Routes

| Route      | Description                                  | Example response                                                              |
| ---------- | -------------------------------------------- | ---------------------------------------------------------------------------- |
| `/`        | Greeting, app info, and Redis visit counter  | `{"app":"starter-app","message":"Hello, world!","version":"1.0.0","visits":1}` |
| `/health`  | Readiness check; `200` only if Redis is up   | `{"status":"ok","redis":"ok"}`                                               |
| `/version` | App name and version                         | `{"app":"starter-app","version":"1.0.0"}`                                     |

If Redis is unreachable, `/health` returns `503` with `{"status":"error","redis":"unreachable"}`.

## Configuration vs secrets

Configuration is split into two files on purpose, to mirror the
ConfigMap / Secret separation you build during training:

| File             | Committed? | Contents                          | Maps to in Kubernetes |
| ---------------- | ---------- | --------------------------------- | --------------------- |
| `app.config.env` | yes        | Non-sensitive config (names, host, port) | **ConfigMap**   |
| `.env`           | no (gitignored) | Secrets (`REDIS_PASSWORD`)   | **Secret**            |

`.env.example` is the template — copy it to `.env` and fill in real values.

## Requirements

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/) (bundled with recent Docker)

## Run with Docker Compose

```bash
cp .env.example .env          # provide the secret(s)
docker compose up --build
```

The app is available on <http://localhost:8080>. Try the routes:

```bash
curl http://localhost:8080/          # visit counter increments each call
curl http://localhost:8080/health
curl http://localhost:8080/version
```

Stop and clean up:

```bash
docker compose down           # keep the Redis volume
docker compose down -v        # also delete the Redis data volume
```

Because Redis data lives on a named volume, the visit counter survives
`docker compose down` and a restart — that persistence is exactly what
makes Redis a StatefulSet candidate.

## Inspecting and troubleshooting

```bash
# Follow logs for both services
docker compose logs -f

# Logs for just one service
docker compose logs -f web
docker compose logs -f redis

# Open a shell in the app container
docker compose exec web sh

# Talk to Redis directly
docker compose exec redis redis-cli --no-auth-warning -a "$REDIS_PASSWORD" GET visits

# Container status (incl. health) and volumes
docker compose ps
docker volume ls | grep redis-data
```

## Run the app locally without Docker (optional)

You still need a Redis instance reachable at `REDIS_HOST:REDIS_PORT`:

```bash
pip install -r requirements.txt
export REDIS_HOST=localhost REDIS_PASSWORD=change-me-in-real-deployments
python app.py
# serves on http://localhost:8080
```

## Project layout

```
.
├── app.py              # The Flask app (3 routes + Redis visit counter)
├── requirements.txt    # Python dependencies (Flask, gunicorn, redis)
├── Dockerfile          # Container image for the web service
├── docker-compose.yml  # web + redis, with a persistent volume
├── app.config.env      # Non-sensitive config  -> ConfigMap target
├── .env.example        # Secret template        -> Secret target
├── .gitignore
├── LICENSE
└── README.md
```

## Training scope (the capstone)

This repo is the **source**. The capstone is to convert it to Kubernetes.
Each piece of the Compose stack has a clear target:

| Source artifact (this repo)          | Kubernetes object to create        |
| ------------------------------------ | ---------------------------------- |
| `web` service                        | **Deployment** + **Service**       |
| `app.config.env`                     | **ConfigMap**                      |
| `.env` (`REDIS_PASSWORD`)            | **Secret**                         |
| `redis` service + `redis-data` volume| **StatefulSet** + **PVC**          |
| Redis reachable inside the cluster   | **(headless) Service** for Redis   |
| Exposing the app outside the cluster | **Ingress**                        |
| `/health` route                      | **liveness / readiness probes**    |

Suggested capstone checklist:

- [ ] Write a Deployment + Service for the `web` app.
- [ ] Move `app.config.env` values into a ConfigMap and mount/inject them.
- [ ] Move `REDIS_PASSWORD` into a Secret and reference it from both workloads.
- [ ] Write a StatefulSet for Redis with a `volumeClaimTemplate` (PVC).
- [ ] Add a headless Service so the app can reach Redis by name.
- [ ] Wire liveness/readiness probes to the `/health` route.
- [ ] Add an Ingress to expose the app.

None of those Kubernetes objects live in this repo by design — they are the
work to be done.
