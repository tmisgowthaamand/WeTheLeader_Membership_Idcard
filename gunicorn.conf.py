# gunicorn.conf.py — memory-optimised for Render free/starter tier
import os

# ── Workers ───────────────────────────────────────────────────────
# 1 worker + threads avoids loading heavy libs (OpenCV, PIL) N times.
# Each gunicorn *process* loads ~150 MB of native libs; threads share that.
workers     = 1
worker_class = "gthread"
threads     = 4

# ── Timeouts ─────────────────────────────────────────────────────
timeout          = 120   # card generation can take a few seconds
graceful_timeout = 30
keepalive        = 5

# ── Binding ──────────────────────────────────────────────────────
port = int(os.environ.get("PORT", 10000))
bind = f"0.0.0.0:{port}"

# ── Logging ──────────────────────────────────────────────────────
accesslog  = "-"
errorlog   = "-"
loglevel   = "info"
access_log_format = '%(h)s "%(r)s" %(s)s %(b)s %(D)sµs'

# ── Memory: recycle workers that grow too large ───────────────────
# After 500 requests, restart the worker to free any leaked memory.
max_requests          = 500
max_requests_jitter   = 50

# ── Preload: load app once, fork workers (saves RAM via copy-on-write)
preload_app = True
