import time
from flask import request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

REQUEST_COUNT = Counter(
    'vaultflow_api_requests_total',
    'Total number of requests handled by the Vaultflow API',
    ['method', 'endpoint', 'http_status']
)

REQUEST_LATENCY = Histogram(
    'vaultflow_api_request_duration_seconds',
    'Latencies of requests handled by Vaultflow API in seconds',
    ['endpoint']
)

def init_metrics(app):
    @app.before_request
    def start_timer():
        request.start_time = time.time()

    @app.after_request
    def log_request(response):
        if request.path == '/metrics':
            return response

        if hasattr(request, 'start_time'):
            latency = time.time() - request.start_time
            REQUEST_LATENCY.labels(endpoint=request.path).observe(latency)

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.path,
            http_status=str(response.status_code)
        ).inc()

        return response

    @app.route('/metrics')
    def metrics_endpoint():
        return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}