from flask import jsonify, current_app, Blueprint, request
from model_service import fetch_model_service_version, predict_sentiment
import metrics
from config import default_config
# from lib_version.version_util import VersionUtil

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

        metrics.predictions_latency.observe(duration)
        metrics.predictions_made.labels(
            model_version=default_config.MODEL_VERSION,
            predicted_label=str(prediction)
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
    Body: {
      "action": "confirm"|"override",
      "originalLabel": 0|1,
      "correctedLabel": 0|1,       # only for override
      "duration": float           # seconds between display and click
    }
    """
    data = request.get_json()
    action = data['action']
    orig = str(data['originalLabel'])
    corr = str(data.get('correctedLabel', orig))
    dur  = float(data['duration'])

    # 1) Decrement pending gauge
    metrics.reviews_pending.dec()

    # 2) Record user latency
    metrics.user_confirmation_latency.observe(dur)

    # 3) If override, bump override counter
    if action == 'override':
        metrics.overrides_by_user.labels(
            original_label=orig,
            corrected_label=corr
        ).inc()

    return '', 204