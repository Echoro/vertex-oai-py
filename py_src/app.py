import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import litellm
import httpx
from py_src.config import load_config
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vertex-oai-py")

# Cache for models
_models_cache = {"data": None, "timestamp": 0}
CACHE_TTL = 3600  # 1 hour

def create_app(config_path: str = "config.yaml"):
    config = load_config(config_path)
    
    # Set environment variables for LiteLLM
    os.environ["VERTEX_PROJECT"] = config.vertex_settings.project
    os.environ["VERTEX_LOCATION"] = config.vertex_settings.location
    
    app = FastAPI(title="Vertex OAI Python Gateway")

    @app.get("/v1/models")
    async def list_models():
        global _models_cache
        now = time.time()
        
        if _models_cache["data"] and (now - _models_cache["timestamp"] < CACHE_TTL):
            return {"object": "list", "data": _models_cache["data"]}

        try:
            # We use litellm's internal logic or fetch directly from Google API
            # For simplicity and parity with the Rust version, we can use httpx to fetch from Google
            # but LiteLLM also has vertex_model_list.
            # Let's try to fetch using litellm's knowledge or fallback to a standard list if needed.
            
            # Since the requirement is to use LiteLLM, let's see if we can get models from it.
            # However, for Vertex, it's often better to just list the supported Gemini models.
            
            # PARITY: The Rust code hits:
            # https://us-central1-aiplatform.googleapis.com/v1beta1/publishers/google/models
            
            url = f"https://{config.vertex_settings.location}-aiplatform.googleapis.com/v1beta1/publishers/google/models"
            if config.vertex_settings.location == "global":
                 url = "https://us-central1-aiplatform.googleapis.com/v1beta1/publishers/google/models"

            # We need an access token. LiteLLM handles this internally, but for direct fetch we'd need google-auth.
            import google.auth
            import google.auth.transport.requests
            
            credentials, project = google.auth.default()
            auth_request = google.auth.transport.requests.Request()
            credentials.refresh(auth_request)
            
            headers = {
                "Authorization": f"Bearer {credentials.token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    logger.error(f"Failed to fetch models from Vertex: {resp.text}")
                    # Fallback to a hardcoded list of common Gemini models if API fails
                    common_models = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"]
                    models_data = [
                        {"id": f"google/{m}", "object": "model", "created": int(now), "owned_by": "google"}
                        for m in common_models
                    ]
                else:
                    data = resp.json()
                    models_data = []
                    for m in data.get("publisherModels", []):
                        name = m.get("name", "")
                        # name is like "publishers/google/models/gemini-1.5-pro-002"
                        parts = name.split('/')
                        if len(parts) >= 4 and "gemini" in parts[3]:
                            model_id = f"{parts[1]}/{parts[3]}"
                            models_data.append({
                                "id": model_id,
                                "object": "model",
                                "created": int(now),
                                "owned_by": parts[1]
                            })
            
            _models_cache["data"] = models_data
            _models_cache["timestamp"] = now
            return {"object": "list", "data": models_data}
            
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            # Fallback
            return {"object": "list", "data": []}

    @app.post("/v1/chat/completions")
    async def chat_completions(request: Request):
        try:
            body = await request.json()
            
            # DYNAMIC MODEL SELECTION
            model = body.get("model")
            if not model:
                raise HTTPException(status_code=400, detail="Model is required")
            
            # LiteLLM needs "vertex_ai/<model_name>"
            # If the user sends "google/gemini-1.5-pro", we convert it.
            # If the user sends "gemini-1.5-pro", we convert it.
            
            if not model.startswith("vertex_ai/"):
                if "/" in model:
                    # e.g. "google/gemini-1.5-pro" -> "vertex_ai/gemini-1.5-pro"
                    parts = model.split('/')
                    model_name = parts[-1]
                    model = f"vertex_ai/{model_name}"
                else:
                    model = f"vertex_ai/{model}"

            messages = body.get("messages", [])
            stream = body.get("stream", False)
            
            completion_kwargs = {
                "model": model,
                "messages": messages,
                "stream": stream,
            }
            
            # Forward other params
            for key in ["temperature", "top_p", "n", "max_tokens", "presence_penalty", "frequency_penalty", "response_format"]:
                if key in body:
                    completion_kwargs[key] = body[key]

            logger.info(f"Forwarding request to Vertex AI: {model}")
            
            response = litellm.completion(**completion_kwargs)
            
            if stream:
                def stream_response():
                    for chunk in response:
                        yield f"data: {chunk.model_dump_json()}\n\n"
                    yield "data: [DONE]\n\n"
                
                return StreamingResponse(stream_response(), media_type="text/event-stream")
            else:
                return JSONResponse(content=response.model_dump())
                
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            # Attempt to extract status code if available from litellm exception
            status_code = getattr(e, "status_code", 500)
            raise HTTPException(status_code=status_code, detail=str(e))

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app, config
