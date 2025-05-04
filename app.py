from flask import Flask

app = Flask(__name__)

@app.route('/healthcheck')
def healthcheck():
    """Returns a simple health check message."""
    return 'App service is running!', 200

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True)