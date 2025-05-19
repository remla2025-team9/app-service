import time
from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from flask import Response

# Create a registry for the metrics
registry = CollectorRegistry(auto_describe=True)

# Define the metrics
reviews_submitted = Counter(
    'reviews_submitted_total',
    'Number of reviews submitted',
    registry=registry
)

predictions_made = Counter(
    'predictions_made_total',
    'Total number of model predictions returned',
    ['predicted_label'],
    registry=registry
)

predictions_latency = Histogram(
    'predictions_latency_seconds',
    'Latency of model predictions in seconds',
    buckets=[0.1, 0.3, 0.5, 1, 2],
    registry=registry
)

overrides_by_user = Counter(
    'overrides_by_user_total',
    'Total number of times users corrected the prediction',
    ['original_label', 'corrected_label'],
    registry=registry
)

reviews_pending = Gauge(
    'reviews_pending_confirmation',
    'Current number of reviews awaiting confirmation',
    registry=registry
)

correct_predictions_rate = Gauge(
    'correct_predictions_rate',
    'Rate of correct predictions made by the model',
    registry=registry
)

user_confirmation_latency = Histogram(
    'user_confirmation_latency_seconds',
    'Latency of user confirmation in seconds',
    buckets=[0.5, 1, 1.5, 2, 3],
    registry=registry
)

def metrics_response():
    """
    Returns the latest metrics in Prometheus format.
    """
    return Response(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)

