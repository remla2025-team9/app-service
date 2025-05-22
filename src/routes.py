from flask import jsonify, current_app, Blueprint, request
from model_service import fetch_model_service_version, predict_sentiment
import metrics
import time
from config import default_config
import logging
# from lib_version.version_util import VersionUtil

logger = logging.getLogger(__name__)

bp = Blueprint('routes', __name__)

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
            lib-version:
              type: string
              example: "1.0.0"
            model-service-version:
              type: string
              example: "1.0.0"
    """
    app_service_version = default_config.APP_VERSION
    # lib_version = VersionUtil.get_version()
    try:
        model_service_version = fetch_model_service_version()
    except Exception:
        model_service_version = "DISCONNECTED"

    response_data = {
        'app-service-version': app_service_version,
        # 'lib-version': lib_version,
        'model-service-version': model_service_version
    }
    return jsonify(response_data), 200

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
        metrics.reviews_submitted.inc()
        metrics.reviews_pending.inc()

        # Start the timer for latency measurement
        start_time = time.monotonic()
        prediction = predict_sentiment(review)
        duration = time.monotonic() - start_time
        predicted_label = 'positive' if prediction == 1 else 'negative'
        metrics.predictions_latency.observe(duration)
        metrics.predictions_made.labels(
            predicted_label=predicted_label
        ).inc()

        response_data = {
            'prediction': predicted_label,
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
    Body: {
      "action": "confirm"|"override",
      "originalLabel": "negative"|"neutral"|"positive",
      "correctedLabel": "negative"|"neutral"|"positive",   # only for override
    }
    """
    data = request.get_json()
    action = data['action']
    orig = str(data['originalLabel'])
    corr = str(data.get('correctedLabel', orig))

    # 1) Decrement pending gauge
    metrics.reviews_pending.dec()

    # 2) If override, bump override counter
    if action == 'override':
        metrics.overrides_by_user.labels(
            original_label=orig,
            corrected_label=corr
        ).inc()
    
    # 3) Modify the correct prediction rate based on the overrides and total predictions
    total_predictions = sum(
        sample.value for sample in metrics.predictions_made.collect()[0].samples
        if sample.name == 'predictions_made_total'
    )
    total_overrides = sum(
        sample.value for sample in metrics.overrides_by_user.collect()[0].samples
        if sample.name == 'overrides_by_user_total'
    )
    print(f"[DEBUG] total_predictions={total_predictions}, total_overrides={total_overrides}", flush=True)
    if total_predictions > 0:
        correct_rate = (total_predictions - total_overrides) / total_predictions
        metrics.correct_predictions_rate.set(correct_rate)
    else:
        metrics.correct_predictions_rate.set(0)

    # 4) Update the true positive
    total_positive = sum(
        sample.value for sample in metrics.predictions_made.collect()[0].samples
        if sample.name == 'predictions_made_total' and sample.labels['predicted_label'] == 'positive'
    )
    override_positive = sum(
        sample.value for sample in metrics.overrides_by_user.collect()[0].samples
        if sample.name == 'overrides_by_user_total' and sample.labels['original_label'] == 'positive'
    )
    if total_positive > 0:
        true_positive_rate = (total_positive - override_positive) / total_positive
        metrics.true_positive_predictions_rate.set(true_positive_rate)
    else:
        metrics.true_positive_predictions_rate.set(0)
    
    # 5) Update the true neutral
    total_neutral = sum(
        sample.value for sample in metrics.predictions_made.collect()[0].samples
        if sample.name == 'predictions_made_total' and sample.labels['predicted_label'] == 'neutral'
    )
    override_neutral = sum(
        sample.value for sample in metrics.overrides_by_user.collect()[0].samples
        if sample.name == 'overrides_by_user_total' and sample.labels['original_label'] == 'neutral'
    )
    if total_neutral > 0:
        true_neutral_rate = (total_neutral - override_neutral) / total_neutral
        metrics.true_neutral_predictions_rate.set(true_neutral_rate)
    else:
        metrics.true_neutral_predictions_rate.set(0)
    
    # 6) Update the true negative
    total_negative = sum(
        sample.value for sample in metrics.predictions_made.collect()[0].samples
        if sample.name == 'predictions_made_total' and sample.labels['predicted_label'] == 'negative'
    )
    override_negative = sum(
        sample.value for sample in metrics.overrides_by_user.collect()[0].samples
        if sample.name == 'overrides_by_user_total' and sample.labels['original_label'] == 'negative'
    )
    if total_negative > 0:
        true_negative_rate = (total_negative - override_negative) / total_negative
        metrics.true_negative_predictions_rate.set(true_negative_rate)
    else:
        metrics.true_negative_predictions_rate.set(0)

    return '', 204