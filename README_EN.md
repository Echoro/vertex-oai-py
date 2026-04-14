# Vertex OAI Python Gateway

[中文版](./README.md)

An OpenAI-compatible gateway for Google Cloud Vertex AI (Gemini models).

This project allows you to use OpenAI's API format to interact with Google's Gemini models hosted on Vertex AI. It's particularly useful for tools like GitHub Copilot and others that expect OpenAI's API format.

## Features

-   **OpenAI API Compatibility**: Implements `/v1/models` and `/v1/chat/completions`.
-   **Vertex AI Integration**: Directly interacts with Google Cloud Vertex AI using `litellm` and `google-cloud-aiplatform`.
-   **Daemon Mode**: Can run as a background service (Unix-like systems).
-   **Model Caching**: Caches the list of available Vertex models for faster responses.
-   **Streaming Support**: Supports server-sent events for streaming chat completions.
-   **Field Preservation**: Logs and preserves important fields like `thought_signatures` for compatibility.
-   **Modern Python Stack**: Built with FastAPI, Uvicorn, and Python 3.13+.

## Project Structure

-   `py_src/`: Core Python implementation.
    -   `app.py`: FastAPI application logic.
    -   `config.py`: Configuration management.
    -   `main.py`: CLI entry point (start/stop/restart/status).
-   `src/`: (Experimental) Rust implementation.
-   `config.yaml`: Service configuration (GCP project, location, server host/port).
-   `main.py`: Entry point for starting the gateway.
-   `test_api.py`: Simple test script for verifying functionality.

## Configuration

Edit `config.yaml` to specify your Google Cloud Project ID and location:

```yaml
vertex_settings:
  project: "your-gcp-project-id"  # Replace with your GCP project ID
  location: "global"             # Replace with your GCP location

server:
  host: "0.0.0.0"
  port: 8080
```

## Installation

This project uses `uv` for dependency management:

```bash
# Install dependencies
uv sync

# Activate the environment
source .venv/bin/activate
```

## Usage

You can manage the gateway using the following commands:

```bash
# Start the server (default in background if daemon mode is supported)
python main.py start

# Start in foreground for debugging
python main.py start --foreground

# Stop the background server
python main.py stop

# Restart the server
python main.py restart

# Check server status
python main.py status
```

## Testing

A basic test script is provided:

```bash
python test_api.py
```

## Deployment

The gateway is designed to run as a daemon service. For production environments, ensure you have appropriate GCP authentication configured (e.g., using `GOOGLE_APPLICATION_CREDENTIALS` or `gcloud auth application-default login`).
