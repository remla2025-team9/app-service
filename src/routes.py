from flask import jsonify, current_app, Blueprint
from .model_service import fetch_model_service_version
from .config import default_config
from lib_version.version_util import VersionUtil

bp = Blueprint('routes', __name__)

@bp.route('/healthcheck')
def healthcheck():
    """Returns a simple health check message."""
    return 'App service is running!', 200

@bp.route('/version')
def version():
    """Returns the application version and model service version."""
    app_service_version = default_config.APP_VERSION
    lib_version = VersionUtil.get_version()
    try:
        model_service_version = fetch_model_service_version()
    except Exception:
        model_service_version = "DISCONNECTED"

    response_data = {
        'app-service-version': app_service_version,
        'lib-version': lib_version,
        'model-service-version': model_service_version
    }
    return jsonify(response_data), 200
