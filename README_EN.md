# 🚀 Vertex OAI Python Gateway

<p align="center">
  <b>English Version</b> |
  <a href="./README.md">中文说明</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

An OpenAI-compatible gateway for **Google Cloud Vertex AI (Gemini models)**.

### 💡 Motivation

This project is an improved Python implementation inspired by [Gallentboy/vertex-oai](https://github.com/Gallentboy/vertex-oai.git). It solves compatibility issues (such as missing `thought_signature` causing 400 errors) when using the latest models like `gemini-3-flash-preview` by leveraging `litellm` as a translation layer.

---

## ✨ Features

-   ✅ **OpenAI API Compatibility**: Implements \`/v1/models\` and \`/v1/chat/completions\`.
-   ☁️ **Vertex AI Integration**: Directly interacts with Google Cloud Vertex AI using \`google-cloud-aiplatform\` and \`litellm\`.
-   👻 **Daemon Mode**: Supports running as a background service on Unix-like systems.
-   ⚡ **Smart Caching**: Caches the list of available Vertex models for faster responses.
-   🌊 **Streaming Support**: Fully supports server-sent events (SSE) for streaming chat completions.
-   🧩 **Field Preservation**: Specifically preserves fields like \`thought_signatures\` for deep GitHub Copilot compatibility.
-   🛠️ **Modern Stack**: Built with FastAPI, Uvicorn, and Python 3.13+.

## 📂 Project Structure

\`\`\`text
├── py_src/          # Core Python source code
│   ├── app.py       # FastAPI routes and logic
│   ├── config.py    # Configuration management
│   └── main.py      # CLI entry point
├── src/             # (Experimental) Rust implementation
├── config.yaml      # Global configuration
├── main.py          # Entry point for the gateway
└── test_api.py      # API automation test script
\`\`\`

## ⚙️ Configuration

Edit \`config.yaml\` to specify your Google Cloud Project ID and location:

\`\`\`yaml
vertex_settings:
  project: "your-gcp-project-id"  # Replace with your GCP project ID
  location: "global"             # Replace with your GCP location

server:
  host: "0.0.0.0"
  port: 8080
\`\`\`

## 🚀 Quick Start

This project uses [uv](https://github.com/astral-sh/uv) for fast dependency management.

\`\`\`bash
# 1. Install dependencies
uv sync

# 2. Activate environment
source .venv/bin/activate

# 3. Start server
python main.py start
\`\`\`

## 🛠️ Commands

| Command | Description |
| :--- | :--- |
| \`python main.py start\` | Start the server (runs in background by default) |
| \`python main.py start --foreground\` | Start in foreground (for debugging) |
| \`python main.py stop\` | Stop the background server |
| \`python main.py restart\` | Restart the server |
| \`python main.py status\` | Check server status |

## 🧪 Testing

Run the provided script to verify functionality:

\`\`\`bash
python test_api.py
\`\`\`

## 🚢 Deployment

Ensure your GCP authentication is configured:
-   Set \`GOOGLE_APPLICATION_CREDENTIALS\` environment variable.
-   Or run \`gcloud auth application-default login\` on your server.

---

<p align="center">Made with ❤️ for the AI Community</p>
