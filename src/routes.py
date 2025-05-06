from flask import jsonify, current_app, Blueprint, request
from model_service import fetch_model_service_version, predict_sentiment, ModelServiceError
from config import default_config

bp = Blueprint('routes', __name__)

@bp.route('/healthcheck')
def healthcheck():
    """Returns a simple health check message."""
    return 'App service is running!', 200

@bp.route('/version')
def version():
    """Returns the application version and model service version."""
    app_service_version = default_config.APP_VERSION
    try:
        model_service_version = fetch_model_service_version()
    except Exception:
        model_service_version = "DISCONNECTED"

    response_data = {
        'app-service-version': app_service_version,
        'model-service-version': model_service_version
    }
    return jsonify(response_data), 200

@bp.route('/predict-sentiment-review', methods=['POST'])
def predict():
    """Predicts sentiment for a given review. 1 for positive, 0 for negative."""
    try:
        data = request.get_json()
        if not data or 'review' not in data:
            return jsonify({'error': 'Invalid input: review field is required'}), 400

        review = data['review']
        if not isinstance(review, str) or not review.strip():
            return jsonify({'error': 'Invalid input: review must be a non-empty string'}), 400

        prediction = predict_sentiment(review)
        response_data = {
            'prediction': prediction,
        }
        return jsonify(response_data), 200

    except ModelServiceError as e:
        return jsonify({'error': f'Model service error: {str(e)}'}), 503
    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        current_app.logger.error(f'Unexpected error in predict endpoint: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500