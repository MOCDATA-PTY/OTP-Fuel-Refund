# Gunicorn configuration file for Fuel Refund Institute
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/var/log/fuelrefund/gunicorn_access.log"
errorlog = "/var/log/fuelrefund/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "fuelrefund_gunicorn"

# Server mechanics
daemon = False
pidfile = "/var/run/fuelrefund/gunicorn.pid"
user = "www-data"
group = "www-data"
tmp_upload_dir = None

# SSL (if using SSL termination at Gunicorn level)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Preload app for better performance
preload_app = True

# Environment variables
raw_env = [
    "DJANGO_SETTINGS_MODULE=mysite.settings",
]

# Hook for when a worker starts
def on_starting(server):
    server.log.info("Starting Fuel Refund Institute Gunicorn server")

def on_reload(server):
    server.log.info("Reloading Fuel Refund Institute Gunicorn server")

def worker_int(worker):
    worker.log.info("Worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker aborted (pid: %s)", worker.pid) 