import time
from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from flask import Response
import re

# Create a registry for the metrics
registry = CollectorRegistry(auto_describe=True)

# Define the metrics
reviews_submitted = Counter(
    'reviews_submitted_total',
    'Number of reviews submitted',
    ['version_label'],
    registry=registry
)

predictions_made = Counter(
    'predictions_made_total',
    'Total number of model predictions returned',
    ['version_label', 'predicted_label'],
    registry=registry
)

predictions_latency = Histogram(
    'predictions_latency_seconds',
    'Latency of model predictions in seconds',
    ['version_label'],
    buckets=[0.1, 0.3, 0.5, 1, 2],
    registry=registry
)

overrides_by_user = Counter(
    'overrides_by_user_total',
    'Total number of times users corrected the prediction',
    ['version_label', 'original_label', 'corrected_label'],
    registry=registry
)

reviews_pending = Gauge(
    'reviews_pending_confirmation',
    'Current number of reviews awaiting confirmation',
    ['version_label'],
    registry=registry
)

correct_predictions_rate = Gauge(
    'correct_predictions_rate',
    'Rate of correct predictions made by the model',
    ['version_label'],
    registry=registry
)

true_positive_predictions_rate = Gauge(
    'true_positive_predictions_rate',
    'Rate of correct positive predictions made by the model',
    ['version_label'],
    registry=registry
)

true_negative_predictions_rate = Gauge(
    'true_negative_predictions_rate',
    'Rate of correct negative predictions made by the model',
    ['version_label'],
    registry=registry
)

true_neutral_predictions_rate = Gauge(
    'true_neutral_predictions_rate',
    'Rate of correct neutral predictions made by the model',
    ['version_label'],
    registry=registry
)

# Function to generate the metrics response
def filtered_metrics_response(registry):
    data = generate_latest(registry).decode('utf-8').splitlines()
    drop_re = re.compile(r'(^[^#].*_created\b|^# (?:HELP|TYPE) .*_created\b)')
    lines = [line for line in data if not drop_re.search(line)]
    return Response('\n'.join(lines) + '\n', mimetype=CONTENT_TYPE_LATEST)