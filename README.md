# App Service

A Flask-based web service that provides sentiment analysis functionality and health monitoring endpoints.

## Overview

This service is part of a microservices architecture and provides:
- **Health Monitoring**: Status checks for service availability
- **Version Information**: Application and dependency version tracking  
- **Sentiment Analysis**: Predict sentiment of text reviews (positive/negative)
- **Metrics Integration**: Prometheus-compatible metrics collection
- **API Documentation**: Interactive Swagger/OpenAPI documentation

## Prerequisites

Before you begin, ensure you have the following installed:
*   [Python](https://www.python.org/) (Version 3.10+ recommended, check `Dockerfile` or `setup-python` step in workflow for specific version used)
*   [pip](https://pip.pypa.io/en/stable/installation/) (usually comes with Python)
*   [Docker](https://www.docker.com/get-started/)
*   [Git](https://git-scm.com/)

## Getting Started

Follow these steps to get the application running locally or via Docker.

### 1. Setup (Local Development)

It's highly recommended to use a virtual environment:

```bash
# Create virtual environment
python -m venv .venv

# Activate it
# Linux/macOS:
source .venv/bin/activate
# Windows (cmd.exe):
.\.venv\Scripts\activate
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

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

### Local Development (Flask Development Server)

Ensure your virtual environment is activated:

```bash
# Run using Python directly
python src/main.py
```

The application will be available at `http://localhost:5000` when the env file was not changed.

### Docker Deployment

Build and run the containerized application:

```bash
# Build the Docker image
docker build -t app-service .

# Run the container
docker run -d -p 5000:5000 --name app-service-container app-service

# Run with environment variables
docker run -d -p 5000:5000 --name app-service-container \
  -e MODEL_SERVICE_URL="http://model-service:8080" \
  app-service
```

**Container Management:**
```bash
# Stop the container
docker stop app-service-container

# Remove the container
docker rm app-service-container

# View logs
docker logs app-service-container
```

## API Endpoints

The service exposes the following REST endpoints:

- **`GET /healthcheck`** - Service health status check
- **`GET /version`** - Application and dependency version information
- **`POST /predict-sentiment-review`** - Sentiment analysis for review text
- **`GET /apidocs`** - Interactive Swagger UI documentation

## API Documentation (Swagger)

This application uses Flasgger to provide interactive API documentation through Swagger UI. The API documentation is automatically generated from the docstrings in the route definitions.

### Accessing the Documentation

Once the application is running, you can access the Swagger UI at:
* `http://localhost:5000/apidocs`

The Swagger UI provides:
* Interactive documentation for all endpoints
* Request/response schemas
* Example values
* The ability to try out API calls directly from the browser

### Documentation Format

Route handlers use YAML-style docstrings that follow the OpenAPI specification:

```python
@bp.route('/example')
def example():
    """
    Example endpoint description.
    ---
    responses:
      200:
        description: Success response
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Success"
    """
```

### Dependencies

The Swagger UI integration requires:
* `flasgger` package (included in requirements.txt)
* Properly formatted YAML docstrings in route handlers

## Configuration

The application uses environment variables for configuration:

### Core Flask Configuration
- **`FLASK_APP`**: Application entry point (Default: `src/main.py`)
- **`FLASK_RUN_HOST`**: Host address for Flask server (Default: `0.0.0.0`)
- **`FLASK_RUN_PORT`**: Port for Flask server (Default: `5000`)
- **`FLASK_DEBUG`**: Debug mode flag (Default: `0`, set to `1` for development only)

### Application Configuration
- **`APP_VERSION`**: Application version string (injected during Docker build)
- **`APP_VERSION_LABEL`**: Version label for Prometheus metrics (Default: `development`)
- **`MODEL_SERVICE_URL`**: URL of the external model service for sentiment analysis

### Security Notes
- Never enable `FLASK_DEBUG=1` in production environments
- Use Docker secrets or orchestration tools for sensitive configuration
- Store the `.env` file locally only (excluded from Git)


## CI/CD Pipeline

This repository implements a comprehensive CI/CD pipeline using GitHub Actions with three main workflows:

### 1. Integration Workflow (`integration.yml`)
**Purpose**: Validates code changes on pull requests

**Triggers**: Pull requests to `main` branch (excludes documentation changes)

**Process**:
- Builds Docker images for multiple architectures (`linux/amd64`, `linux/arm64`)
- Validates Dockerfile and build process
- **Does not push images** - validation only

### 2. Delivery Workflow (`delivery.yml`)  
**Purpose**: Automatic pre-release versioning on main branch

**Triggers**: Direct pushes to `main` branch

**Process**:
- Automatically creates pre-release tags (e.g., `v1.2.0-pre.1`)
- Increments version numbers using semantic versioning
- Prepares repository for continuous development
- **Does not build or deploy** - tagging only

### 3. Deployment Workflow (`deployment.yml`)
**Purpose**: Manual stable releases and container deployment

**Triggers**: Manual workflow dispatch with version bump options (`patch`, `minor`, `major`)

**Process**:
1. Creates stable release commit and Git tag
2. Generates GitHub release with changelog
3. Builds and pushes multi-architecture Docker images to GHCR
4. Tags images as `latest` and version-specific (e.g., `v1.2.0`)
5. Creates next pre-release tag for continued development

**Usage**:
1. Go to GitHub Actions → "Deployment" workflow
2. Click "Run workflow" 
3. Select version bump level (`patch`/`minor`/`major`)
4. Run from `main` branch

### 4. Canary Feature Deployment (`canary_feature_deployment.yml`)
**Purpose**: Deploy experimental features for testing

**Triggers**: Manual workflow dispatch with optional experiment name

**Process**:
- Builds and pushes feature-specific Docker images
- Creates `canary` tag for experimental deployments
- Generates version tags like `version.beta-feature-name`
- Supports deployment from any branch for feature testing

**Container Registry**: All images are pushed to GitHub Container Registry (GHCR)
