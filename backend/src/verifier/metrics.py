from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from flask import Blueprint, Response
import time
import logging

logger = logging.getLogger("LOGGER")

metrics_bp = Blueprint('metrics', __name__)

# Verification Metrics
verification_duration_seconds = Histogram(
    'verification_duration_seconds', 
    'Time spent verifying a presentation',
    ['method', 'status']  # method: bbs or sd_jwt, status: success or error
)

verification_attempts_total = Counter(
    'verification_attempts_total',
    'Total number of verification attempts',
    ['method', 'status']
)

# Initialize metrics with default labels to ensure they appear in Prometheus immediately
for method in ['bbs', 'sd_jwt']:
    for status in ['success', 'failure']:
        verification_attempts_total.labels(method=method, status=status).inc(0)
        verification_duration_seconds.labels(method=method, status=status)

@metrics_bp.route('/metrics')
def metrics():
    # Force collection of all metrics
    return Response(generate_latest(), mimetype='text/plain')
