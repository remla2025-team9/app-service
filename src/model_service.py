import requests
import logging
from config import default_config

logger = logging.getLogger(__name__)

try:
    model_service_url_config = default_config.MODEL_SERVICE_URL.rstrip('/')
except:
    logger.error("MODEL_SERVICE_URL is not set or invalid in the configuration.")
    model_service_url_config = None

def fetch_model_service_version():
    """
    Fetches the version from the MODEL_SERVICE_URL/version endpoint.
    Returns the version string or "Unknown" on any failure.
    """
    if not model_service_url_config:
        logger.warning("MODEL_SERVICE_URL is not set. Cannot fetch model version.")
        raise ValueError("MODEL_SERVICE_URL is not set. Cannot fetch model version.")

    model_version_endpoint = f"{model_service_url_config}/version"
    logger.info(f"Attempting to fetch model service version from: {model_version_endpoint}")

    try:
        response = requests.get(model_version_endpoint, timeout=5)
        response.raise_for_status()

        data = response.json()
        if 'version' in data and isinstance(data['version'], str):
            logger.info(f"Successfully fetched model version: {data['version']}")
            return data['version']
        else:
            logger.error(f"Invalid JSON structure from model service: {data} at {model_version_endpoint}")
            raise ValueError("Invalid JSON structure: 'version' key not found or not a string.")
    except Exception as e:
        logger.error(f"Failed to fetch or process model service version from {model_version_endpoint}: {e}")
        raise ValueError("Failed to fetch model service version.")
    
def predict_sentiment(review):
    """
    Sends a review to the model service for sentiment prediction.
    Returns the prediction result or raises an error on failure.
    """
    if not model_service_url_config:
        logger.warning("MODEL_SERVICE_URL is not set.")
        raise ValueError("MODEL_SERVICE_URL is not set.")

    predict_endpoint = f"{model_service_url_config}/v1/predict"
    logger.info(f"Attempting to send review to model service at: {predict_endpoint}")

    try:
        response = requests.post(
            predict_endpoint, 
            json={'review': review}, 
            timeout=5
            )
        response.raise_for_status()

        data = response.json()
        if 'prediction' in data and isinstance(data['prediction'], int):
            logger.info(f"Successfully received prediction: {data['prediction']}")
            return data['prediction']
        else:
            logger.error(f"Invalid JSON structure from model service: {data} at {predict_endpoint}")
            raise ValueError("Invalid JSON structure: 'prediction' key not found or not a string.")
    except Exception as e:
        logger.error(f"Failed to fetch or process prediction from {predict_endpoint}: {e}")
        raise ValueError("Failed to fetch prediction from model service.")
