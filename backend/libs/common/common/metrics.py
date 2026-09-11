"""Prometheus metrics endpoint shared by every service.

Each service reports request counts/latency plus its own business counters.
The endpoint is served (but not advertised in the OpenAPI schema) at ``/metrics``.
"""

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

http_requests = Counter(
    "http_requests_total", "HTTP requests", ["service", "method", "path", "status"]
)
http_duration = Histogram(
    "http_request_duration_seconds", "HTTP request latency", ["service", "path"]
)


async def metrics_endpoint(request: Request) -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def add_metrics_route(app: FastAPI) -> None:
    app.add_api_route("/metrics", metrics_endpoint, methods=["GET"], include_in_schema=False)