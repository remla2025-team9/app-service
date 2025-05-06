import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Set configuration variables from environment variables
DEBUG_MODE = os.getenv('FLASK_DEBUG', '0') == '1'
HOST = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
try:
    PORT = int(os.getenv('FLASK_RUN_PORT', '5000'))
except ValueError:
    print("Warning: Invalid FLASK_RUN_PORT value, using default 5000.")
    PORT = 5000
MODEL_SERVICE_URL = os.getenv('MODEL_SERVICE_URL')

APP_VERSION = os.getenv('APP_VERSION', 'unknown-local')

app.config['MODEL_SERVICE_URL'] = MODEL_SERVICE_URL
app.config['APP_VERSION'] = APP_VERSION


@app.route('/healthcheck')
def healthcheck():
    """Returns a simple health check message."""
    return 'App service is running!', 200


@app.route('/version')
def version():
    """Returns the application version."""
    return {
        'app-service-version': app.config['APP_VERSION'],
        'model-service-version': "Unknown"
    }, 200


if __name__ == '__main__':
  app.run(host=HOST, port=PORT, debug=DEBUG_MODE)