import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEBUG_MODE = os.getenv('FLASK_DEBUG', '0') == '1'
    HOST = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    try:
        PORT = int(os.getenv('FLASK_RUN_PORT', '5000'))
    except ValueError:
        print("Warning: Invalid FLASK_RUN_PORT value, using default 5000.")
        PORT = 5000

    MODEL_SERVICE_URL = os.getenv('MODEL_SERVICE_URL')
    APP_VERSION = os.getenv('APP_VERSION', 'NOT SET')

default_config = Config()