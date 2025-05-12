# app-service

Flask app

## Description

This service currently provides:
*   A healthcheck route (`/healthcheck`) that displays the health status of the flask service
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
python src/main.py

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
#   -e MODEL_SERVICE_URL="http://localhost:8080/" \
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
*   `MODEL_SERVICE_URL`: URL of the model service. Should be set to communicate with the model service.

Use Docker secrets, orchestration tool secrets management, or pass via `-e` for non-sensitive runtime config.

## Continuous Integration

This repository uses GitHub Actions for Continuous Integration. The workflow is defined in `.github/workflows/integration.yml`.

On every pull request targeting the `main` branch, the workflow automatically:
1.  Checks out the code.
2.  Builds the Docker image for `linux/amd64` and `linux/arm64` to validate the build process (without pushing the image).
3.  


## Continuous Delivery (Pre-Release Tagging)

This repository utilizes GitHub Actions for a simple Continuous Delivery process focused on automatic version tagging on the `main` branch. The workflow is defined in `.github/workflows/delivery.yml`.

**Process:**

1.  **Trigger:** The workflow runs automatically whenever changes are pushed to the `main` branch.
2.  **Versioning:** It uses the `mathieudutour/github-tag-action` to:
    *   Check the latest existing Git tag.
    *   Determine the next appropriate version based on semantic versioning rules, specifically for pre-releases.
    *   If the previous tag was a stable release (e.g., `v1.2.0`), it calculates the next *pre-patch* version (e.g., `v1.2.1-pre.0`).
    *   If the previous tag was already a pre-release (e.g., `v1.2.1-pre.0`), it increments the pre-release identifier (e.g., `v1.2.1-pre.1`).
    *   If no previous tags exist, it starts with `v0.1.0-pre.0`.
3.  **Tag Creation:** A new Git tag (prefixed with `v` and appended with `-pre.[number]`) corresponding to the calculated version is automatically created and pushed to the repository.

**Important Notes:**

*   This workflow **only creates pre-release Git tags** on the `main` branch. It does **not** create formal GitHub Releases or trigger deployments.
*   Full releases (stable tags without the `-pre` suffix) are intentionally disabled in this workflow (`release_branches: '_NONE_'`) and would need to be created via the deployment workflow manually

## Deployment Workflow (Manual Trigger)

This repository includes a GitHub Actions workflow for building and deploying stable releases. The workflow is defined in `.github/workflows/deployment.yml`.

**Process:**

1.  **Trigger:** This workflow is **not** automatic. It must be triggered manually via the GitHub Actions UI (`workflow_dispatch`). You can typically trigger it from the `main` branch.
2.  **Versioning:**
    *   The workflow first determines the target *stable* version number.
    *   If the workflow was triggered by pushing a stable tag (e.g., `v1.2.0`), it uses that exact version number (stripping the `v`).
    *   If triggered manually (e.g., on the `main` branch), it finds the *most recent* tag (usually a pre-release like `v1.2.0-pre.5`) and strips the `-pre.*` suffix to get the base stable version (e.g., `1.2.0`).
    *   It then creates a new, stable Git tag matching this resolved version (e.g., `1.2.0`) if it doesn't already exist.
3.  **Docker Build & Push:**
    *   Sets up Docker Buildx for multi-platform builds (`linux/amd64`, `linux/arm64`).
    *   Logs into the GitHub Container Registry (GHCR).
    *   Builds the Docker image, injecting the resolved stable version number as the `APP_VERSION` build argument (making the application version-aware).
    *   Pushes the image to GHCR using two tags:
        *   `latest`
        *   The resolved stable version number (e.g., `ghcr.io/owner/repo:1.2.0`)
    *   Utilizes the registry for build caching (`type=registry`) to speed up subsequent builds.
4.  **Next Pre-Release Tag (if triggered on `main`):**
    *   *After successfully creating the stable tag and pushing the image*, if the workflow was triggered on the `main` branch, it automatically calculates and creates the *next* pre-release patch tag (e.g., if `1.2.0` was just released, it creates `v1.2.1-pre.0`). This prepares the repository for the next cycle of development and pre-releases based on the `main` branch.

**How to Use:**

1.  Navigate to the "Actions" tab of the repository on GitHub.
2.  Select the "Deployment" workflow from the list on the left.
3.  Click the "Run workflow" dropdown button.
4.  Typically, you will run it from the `main` branch.
5.  Click "Run workflow".

**Important Notes:**

*   This workflow creates **stable Git tags** (e.g., `1.2.0`) and pushes **stable container images** to GHCR.
*   The final step of creating the *next* pre-release tag only occurs when manually dispatched from the `main` branch, facilitating continuous development after a release.
