from flask import Flask
from flask_cors import CORS
import logging
from routes import bp
from config import default_config

# Configure basic logging
logging.basicConfig(level=logging.INFO if not default_config.DEBUG_MODE else logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app instance
app = Flask(__name__)

# Apply configuration from config.py
app.config['DEBUG'] = default_config.DEBUG_MODE

# Initialize extensions
CORS(app)

# Log some startup info
logger.info(f"Flask app '{__name__}' initialized.")
logger.info(f"Debug mode: {app.config['DEBUG']}")

if __name__ == '__main__':
    app.register_blueprint(bp)

    logger.info(f"Starting server on http://{default_config.HOST}:{default_config.PORT}")
    app.run(
        host=default_config.HOST,
        port=default_config.PORT,
        debug=default_config.DEBUG_MODE
    )