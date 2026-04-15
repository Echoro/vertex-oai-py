import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import litellm
import httpx
from py_src.config import load_config
import logging
import time
import json
from copy import deepcopy

# Configure logging to console and file
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vertex-oai-py")

# Cache for models
_models_cache = {"data": None, "timestamp": 0}
CACHE_TTL = 3600  # 1 hour

def sanitize_response(response_obj, debug_mode=False):
    """
    LOGS only if debug_mode is True, and preserves all fields.
    Ensures OpenAI basic compatibility (non-null content).
    """
    raw_data = response_obj if isinstance(response_obj, dict) else response_obj.model_dump()

    # 仅在调试模式开启时打印详细响应
    if debug_mode:
        logger.info(f">>> SERVER TO COPILOT (RAW): {json.dumps(raw_data)}")

    sanitized = deepcopy(raw_data)

    if "choices" in sanitized:
        for choice in sanitized["choices"]:
            if "message" in choice:
                if choice["message"].get("content") is None:
                    choice["message"]["content"] = ""
            if "delta" in choice:
                if choice["delta"].get("content") is None:
                    choice["delta"]["content"] = ""

    return sanitized

def create_app(config_path: str = "config.yaml"):
    config = load_config(config_path)
    debug_mode = config.server.debug

    app = FastAPI(title="Vertex OAI Python Gateway")
    @app.get("/v1/models")
    async def list_models():
        global _models_cache
        now = time.time()
        if _models_cache["data"] and (now - _models_cache["timestamp"] < CACHE_TTL):
            return {"object": "list", "data": _models_cache["data"]}
        try:
            url = "https://us-central1-aiplatform.googleapis.com/v1beta1/publishers/google/models"
            import google.auth
            import google.auth.transport.requests
            scopes = ["https://www.googleapis.com/auth/cloud-platform"]
            credentials, project = google.auth.default(scopes=scopes)
            auth_request = google.auth.transport.requests.Request()
            credentials.refresh(auth_request)
            headers = {
                "Authorization": f"Bearer {credentials.token}",
                "Content-Type": "application/json",
                "x-goog-user-project": config.vertex_settings.project
            }
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    raise HTTPException(status_code=resp.status_code, detail="Failed to fetch models")
                data = resp.json()
                models_data = []
                for m in data.get("publisherModels", []):
                    name = m.get("name", "")
                    launch_stage = m.get("launchStage")
                    if "gemini" in name.lower() and launch_stage in ["GA", "PUBLIC_PREVIEW"]:
                        parts = name.split('/')
                        if len(parts) >= 4:
                            models_data.append({
                                "id": f"{parts[1]}/{parts[3]}",
                                "object": "model",
                                "created": int(now),
                                "owned_by": parts[1]
                            })
            _models_cache["data"] = models_data
            _models_cache["timestamp"] = now
            return {"object": "list", "data": models_data}
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    # ... (models endpoint simplified for brevity in this replace call context)

    @app.post("/v1/chat/completions")
    async def chat_completions(request: Request):
        try:
            body = await request.json()
            if debug_mode:
                logger.info(f"<<< COPILOT TO SERVER (OPENAI): {json.dumps(body)}")

            model = body.get("model")
            if not model:
                raise HTTPException(status_code=400, detail="Model is required")

            model_id = model.split('/')[-1] if '/' in model else model
            vertex_model = f"vertex_ai/{model_id}"

            location = config.vertex_settings.location
            if "gemini-3" in model_id:
                location = "global"

            messages = body.get("messages", [])
            stream = body.get("stream", False)

            completion_kwargs = {
                "model": vertex_model,
                "messages": messages,
                "stream": stream,
                "vertex_project": config.vertex_settings.project,
                "vertex_location": location,
            }

            for key in ["temperature", "top_p", "n", "max_tokens", "presence_penalty", "frequency_penalty", "response_format", "tools", "tool_choice"]:
                if key in body:
                    completion_kwargs[key] = body[key]

            if debug_mode:
                logger.info(f"--- SERVER TO VERTEX (ARGS): {json.dumps(completion_kwargs, default=str)}")

            if stream:
                response = litellm.completion(**completion_kwargs)
                def stream_response():
                    try:
                        for chunk in response:
                            sanitized = sanitize_response(chunk, debug_mode)
                            yield f"data: {json.dumps(sanitized)}\n\n"
                        yield "data: [DONE]\n\n"
                    except Exception as e:
                        logger.error(f"Streaming error: {str(e)}")
                        yield f"data: {json.dumps({'error': {'message': str(e)}})}\n\n"
                        yield "data: [DONE]\n\n"
                return StreamingResponse(stream_response(), media_type="text/event-stream")
            else:
                response = litellm.completion(**completion_kwargs)
                sanitized = sanitize_response(response, debug_mode)
                return JSONResponse(content=sanitized)

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return JSONResponse(status_code=500, content={"detail": str(e)})

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app, config
