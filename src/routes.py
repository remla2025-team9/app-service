from flask import jsonify, current_app, Blueprint, request
from model_service import fetch_model_service_version, predict_sentiment
import metrics
import time
from config import default_config
import logging
from lib_version.version_util import VersionUtil

logger = logging.getLogger(__name__)

bp = Blueprint('routes', __name__)

app_version_label = getattr(default_config, 'APP_VERSION_LABEL', 'unknown_label')

@bp.route('/healthcheck')
def healthcheck():
    """
    Returns a health check message.
    ---
    responses:
      200:
        description: Service is healthy
        schema:
          type: string
          example: App service is running!
    """
    return 'App service is running!', 200

@bp.route('/version')
def version():
    """
    Returns version information for all services.
    ---
    produces:
      - application/json
    responses:
      200:
        description: Version information
        schema:
          type: object
          properties:
            app-service-version:
              type: string
              example: "1.0.0"
            model-service-version:
              type: string
              example: "1.0.0"
            lib-version:
              type: string
              example: "1.0.0"
    """
    app_service_version = default_config.APP_VERSION
    try:
      lib_version = VersionUtil.get_version()
    except Exception as e:
        lib_version = "DISCONNECTED"
    try:
        model_service_version = fetch_model_service_version()
    except Exception:
        model_service_version = "DISCONNECTED"

    response_data = {
        'app-service-version': app_service_version,
        'model-service-version': model_service_version,
        'lib-version': lib_version,
    }
    return jsonify(response_data), 200

@bp.route('/metrics', methods=['GET'])
def metrics_endpoint():
    """
    Returns Prometheus metrics.
    ---
    produces:
      - text/plain
    responses:
      200:
        description: Metrics data in Prometheus format
        schema:
          type: string
          example: 'app_service_metrics{version="1.0.0"} 1.0'
    """
    return metrics.filtered_metrics_response(metrics.registry), 200

@bp.route('/predict-sentiment-review', methods=['POST'])
def predict():
    """
    Submit a review message to be predicted as positive or negative.
    ---
    consumes:
      - application/json
    parameters:
      - name: review
        in: body
        required: true
        schema:
          type: object
          properties:
            review:
              type: string
        description: The review to be analyzed
    responses:
      200:
        description: Prediction result
        schema:
          type: object
          properties:
            prediction:
              type: integer
              enum: [0, 1]
              description: 1 for positive, 0 for negative
      400:
        description: Invalid input
        schema:
          type: object
          properties:
            error:
              type: string
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        data = request.get_json()
        if not data or 'review' not in data:
            return jsonify({'error': 'Invalid input: review field is required'}), 400

        review = data['review']
        if not isinstance(review, str) or not review.strip():
            return jsonify({'error': 'Invalid input: review must be a non-empty string'}), 400
        
        # Increment the reviews submitted counter
        metrics.reviews_submitted.labels(version_label=app_version_label).inc()
        metrics.reviews_pending.labels(version_label=app_version_label).inc()

        # Start the timer for latency measurement
        start_time = time.monotonic()
        prediction = predict_sentiment(review)
        duration = time.monotonic() - start_time
        predicted_label = 'positive' if prediction == 1 else 'negative'
        metrics.predictions_latency.labels(version_label=app_version_label).observe(duration)
        metrics.predictions_made.labels(
            version_label=app_version_label,
            predicted_label=predicted_label
        ).inc()

        response_data = {
            'prediction': prediction,
        }
        return jsonify(response_data), 200

    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        current_app.logger.error(f'Unexpected error in predict endpoint: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500
  
@bp.route('/reviews/confirm', methods=['POST'])
def confirm_review():
    """
    Handles the confirmation/override of a review.
    ---
    consumes:
      - application/json
    parameters:
      - name: confirmation
        in: body
        required: true
        schema:
          type: object
          properties:
            action:
              type: string
              enum: [confirm, override]
              description: Action to take on the review
            originalLabel:
              type: string
              enum: [negative, neutral, positive]
              description: Original label of the review
            correctedLabel:
              type: string
              enum: [negative, neutral, positive]
              description: Corrected label of the review (only for override)
    responses:
      204:
        description: Review confirmed/overridden successfully
      400:
        description: Invalid input
        schema:
          type: object
          properties:
            error:
              type: string
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
    """
    data = request.get_json()
    action = data['action']
    orig = str(data['originalLabel'])
    corr = str(data.get('correctedLabel', orig))

    # 1) Decrement pending gauge
    metrics.reviews_pending.labels(version_label=app_version_label).dec()

    # 2) If override, bump override counter
    if action == 'override':
        metrics.overrides_by_user.labels(
            version_label=app_version_label,
            original_label=orig,
            corrected_label=corr
        ).inc()
    
    # 3) Modify the correct prediction rate based on the overrides and total predictions
    
    # Calculate total predictions for the current app_version_label.
    total_predictions = sum(
        sample.value
        for metric_family in metrics.predictions_made.collect()
        for sample in metric_family.samples
        if sample.labels.get('version_label') == app_version_label
    )

    # Calculate total overrides for the current app_version_label.
    total_overrides = sum(
        sample.value
        for metric_family in metrics.overrides_by_user.collect()
        for sample in metric_family.samples
        if sample.labels.get('version_label') == app_version_label
    )
    
    logger.debug(f"[DEBUG] ConfirmReview - Version: {app_version_label}, TotalPredictions: {total_predictions}, TotalOverrides: {total_overrides}")
    
    if total_predictions > 0:
        correct_rate = (total_predictions - total_overrides) / total_predictions
        metrics.correct_predictions_rate.labels(version_label=app_version_label).set(max(0, correct_rate))
    else:
        metrics.correct_predictions_rate.labels(version_label=app_version_label).set(0)

    # 4) Update the true positive rate
    
    # Calculate total predictions originally labeled as 'positive' for the current app_version_label.
    total_positive_predictions = sum(
        sample.value
        for metric_family in metrics.predictions_made.collect()
        for sample in metric_family.samples
        if sample.labels.get('version_label') == app_version_label and \
           sample.labels.get('predicted_label') == 'positive'
    )

    # Calculate total overrides where the original label was 'positive' for the current app_version_label.
    overridden_when_positive = sum(
        sample.value
        for metric_family in metrics.overrides_by_user.collect()
        for sample in metric_family.samples
        if sample.labels.get('version_label') == app_version_label and \
           sample.labels.get('original_label') == 'positive'
    )

    if total_positive_predictions > 0:
        # Calculate true positive rate: (positive predictions - overrides from positive) / total positive predictions
        true_positive_rate = (total_positive_predictions - overridden_when_positive) / total_positive_predictions
        metrics.true_positive_predictions_rate.labels(version_label=app_version_label).set(max(0, true_positive_rate))
    else:
        metrics.true_positive_predictions_rate.labels(version_label=app_version_label).set(0)
    
    # 5) Update the true neutral rate
    
    # Calculate total predictions originally labeled as 'neutral' for the current app_version_label.
    total_neutral_predictions = sum(
        sample.value
        for metric_family in metrics.predictions_made.collect()
        for sample in metric_family.samples
        if sample.labels.get('version_label') == app_version_label and \
           sample.labels.get('predicted_label') == 'neutral'
    )

    # Calculate total overrides where the original label was 'neutral' for the current app_version_label.
    overridden_when_neutral = sum(
        sample.value
        for metric_family in metrics.overrides_by_user.collect()
        for sample in metric_family.samples
        if sample.labels.get('version_label') == app_version_label and \
           sample.labels.get('original_label') == 'neutral'
    )

    if total_neutral_predictions > 0:
        true_neutral_rate = (total_neutral_predictions - overridden_when_neutral) / total_neutral_predictions
        metrics.true_neutral_predictions_rate.labels(version_label=app_version_label).set(max(0, true_neutral_rate))
    else:
        metrics.true_neutral_predictions_rate.labels(version_label=app_version_label).set(0)
    
    # 6) Update the true negative rate

    # Calculate total predictions originally labeled as 'negative' for the current app_version_label.
    total_negative_predictions = sum(
        sample.value
        for metric_family in metrics.predictions_made.collect()
        for sample in metric_family.samples
        if sample.labels.get('version_label') == app_version_label and \
           sample.labels.get('predicted_label') == 'negative'
    )

    # Calculate total overrides where the original label was 'negative' for the current app_version_label.
    overridden_when_negative = sum(
        sample.value
        for metric_family in metrics.overrides_by_user.collect()
        for sample in metric_family.samples
        if sample.labels.get('version_label') == app_version_label and \
           sample.labels.get('original_label') == 'negative'
    )

    if total_negative_predictions > 0:
        true_negative_rate = (total_negative_predictions - overridden_when_negative) / total_negative_predictions
        metrics.true_negative_predictions_rate.labels(version_label=app_version_label).set(max(0, true_negative_rate))
    else:
        metrics.true_negative_predictions_rate.labels(version_label=app_version_label).set(0)

    return '', 204