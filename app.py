"""
Hello-world Flask application with a stateful backend.

A deliberately small web service used as the starting point for a
Kubernetes support training capstone. It talks to a Redis backing
service (a visit counter) and reads its configuration from the
environment, split into two groups so the conversion to Kubernetes is
obvious:

  * Non-sensitive values (APP_NAME, GREETING, REDIS_HOST, ...) come from
    app.config.env  ->  becomes a ConfigMap.
  * Sensitive values (REDIS_PASSWORD) come from .env (gitignored)
                      ->  becomes a Secret.

The Redis service keeps its data on a persistent volume, which is the
piece that later maps to a StatefulSet + PersistentVolumeClaim.
"""

import os

import redis
from flask import Flask, jsonify

app = Flask(__name__)

# --- Non-sensitive config (ConfigMap candidate) ---
APP_NAME = os.environ.get("APP_NAME", "starter-app")
APP_VERSION = os.environ.get("APP_VERSION", "1.0.0")
GREETING = os.environ.get("GREETING", "Hello, world!")
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))

# --- Sensitive config (Secret candidate) ---
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")

# Single shared client. The backing service (Redis) is the stateful
# component that maps to a StatefulSet in Kubernetes.
cache = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    socket_connect_timeout=2,
    decode_responses=True,
)


@app.route("/")
def index():
    """Return a greeting, basic app info, and the visit count from Redis."""
    visits = cache.incr("visits")
    return jsonify(
        message=GREETING,
        app=APP_NAME,
        version=APP_VERSION,
        visits=visits,
    )


@app.route("/health")
def health():
    """Readiness check. Returns 200 only if the Redis backend is reachable."""
    try:
        cache.ping()
    except redis.RedisError:
        return jsonify(status="error", redis="unreachable"), 503
    return jsonify(status="ok", redis="ok"), 200


@app.route("/version")
def version():
    """Return the app name and version."""
    return jsonify(app=APP_NAME, version=APP_VERSION)


if __name__ == "__main__":
    # Local development server only. In the container the app is served
    # by gunicorn (see Dockerfile) for a more production-like setup.
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
