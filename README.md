# app-service

Flask app

## Description

This service currently provides:
*   A healthchck route (`/healthcheck`) that displays the health status of the flask service
*   A Dockerfile for building a container image.
*   A GitHub Actions workflow for basic CI/CD

## Prerequisites

Before you begin, ensure you have the following installed:
*   [Python](https://www.python.org/) (Version 3.10+ recommended, check `Dockerfile` or `setup-python` step in workflow for specific version used)
*   [pip](https://pip.pypa.io/en/stable/installation/) (usually comes with Python)
*   [Docker](https://www.docker.com/get-started/)

## Getting Started

Follow these steps to get the application running locally or via Docker.

### 1. Setup (Local Development)

It's highly recommended to use a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Linux/macOS:
source venv/bin/activate
# Windows (cmd.exe):
.\venv\Scripts\activate
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

This project uses environment variables for configuration. A template file is provided to help you set up your local environment.

*   **Copy the template:** Create your local environment file by copying the template:
    ```bash
    # On Linux/macOS:
    cp .env.template .env

    # On Windows (Command Prompt):
    copy .env.template .env
    ```

*   **Edit `.env`:** Open the newly created `.env` file in your text editor.
*   **Fill in values:** Replace the placeholder values with your actual local development settings.
*   **Important:** The `.env` file should **NOT** be committed to Git (it should be listed in your `.gitignore`). It's for your local setup only.

## Running the Application

### Locally (using Flask development server)

Make sure your virtual environment is activated.

```bash
# Simple run (uses defaults, potentially debug=True from app.py's __main__ block)
python app.py

# OR Recommended: Use the Flask CLI (respects FLASK_APP, FLASK_DEBUG env vars)
# Set debug mode via environment variable if needed (0=off, 1=on)
# export FLASK_DEBUG=1 # Linux/macOS
# $env:FLASK_DEBUG=1  # PowerShell
# set FLASK_DEBUG=1   # Windows CMD
flask run --host=0.0.0.0 --port=5000
```
The application will be accessible at `http://localhost:5000`.

### Using Docker

First, build the Docker image:

```bash
# Build the image and tag it (replace 'my-flask-app' with your preferred tag)
docker build -t my-flask-app .
```

Then, run the container:

```bash
# Run in detached mode (-d), map port 5000 (-p), name the container
docker run -p 5000:5000 app-service

# You can override environment variables during run time:
# docker run -d -p 5000:5000 --name my-running-app \
#   -e GREETING_MESSAGE="Hello from the docker run command!" \
#   my-flask-app
```
The application will be accessible at `http://localhost:5000`.

To stop the container:
```bash
docker stop app-service
```
To remove the container:
```bash
docker rm app-service
```

## API Endpoints

*   `GET /healthcheck`: Displays the health status of the flask service.

## Configuration / Environment Variables

The application uses environment variables for configuration:

*   `FLASK_APP`: (Default: `app.py`) Specifies the application file for Flask.
*   `FLASK_RUN_HOST`: (Default: `0.0.0.0`) Host Flask listens on inside the container.
*   `FLASK_DEBUG`: (Default: `0`) Set to `1` to enable Flask's debug mode (Do NOT use `1` in production).
** Use Docker secrets, orchestration tool secrets management, or pass via `-e` for non-sensitive runtime config.

## Continuous Integration

This repository uses GitHub Actions for Continuous Integration. The workflow is defined in `.github/workflows/integration.yml`.

On every pull request targeting the `main` branch, the workflow automatically:
1.  Checks out the code.
2.  Builds the Docker image for `linux/amd64` and `linux/arm64` to validate the build process (without pushing the image).