import multiprocessing

# worker_class = "gthread"
worker_class = "sync"
threads = 4
workers = min(2, multiprocessing.cpu_count())
bind = "0.0.0.0:80"
timeout = 90
keepalive = 3600
preload_app = True
