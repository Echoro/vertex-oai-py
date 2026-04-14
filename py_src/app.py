import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import litellm
import httpx
from py_src.config import load_config
import logging
import time
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vertex-oai-py")

# Cache for models
_models_cache = {"data": None, "timestamp": 0}
CACHE_TTL = 3600  # 1 hour

def create_app(config_path: str = "config.yaml"):
    config = load_config(config_path)
    
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
                    logger.error(f"Failed to fetch models from Vertex: {resp.text}")
                    raise HTTPException(status_code=resp.status_code, detail="Failed to fetch models from Vertex")
                
                data = resp.json()
                models_data = []
                publisher_models = data.get("publisherModels", [])
                
                for m in publisher_models:
                    name = m.get("name", "")
                    launch_stage = m.get("launchStage")
                    
                    is_gemini = "gemini" in name.lower()
                    is_stable = launch_stage in ["GA", "PUBLIC_PREVIEW"]
                    
                    if is_gemini and is_stable:
                        parts = name.split('/')
                        if len(parts) >= 4:
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
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/v1/chat/completions")
    async def chat_completions(request: Request):
        try:
            body = await request.json()
            
            model = body.get("model")
            if not model:
                raise HTTPException(status_code=400, detail="Model is required")
            
            # Map request model to vertex_ai/<model_id>
            model_id = model.split('/')[-1] if '/' in model else model
            vertex_model = f"vertex_ai/{model_id}"

            # Rust logic: gemini-3 models use "global" location
            location = config.vertex_settings.location
            if "gemini-3" in model_id:
                location = "global"
                logger.info(f"Detected Gemini-3 model, switching location to global")

            messages = body.get("messages", [])
            stream = body.get("stream", False)
            
            completion_kwargs = {
                "model": vertex_model,
                "messages": messages,
                "stream": stream,
                "vertex_project": config.vertex_settings.project,
                "vertex_location": location,
            }
            
            # Forward other params
            for key in ["temperature", "top_p", "n", "max_tokens", "presence_penalty", "frequency_penalty", "response_format"]:
                if key in body:
                    completion_kwargs[key] = body[key]

            logger.info(f"Forwarding request to Vertex AI ({location}): {vertex_model}")
            
            if stream:
                response = litellm.completion(**completion_kwargs)
                def stream_response():
                    try:
                        for chunk in response:
                            yield f"data: {chunk.model_dump_json()}\n\n"
                        yield "data: [DONE]\n\n"
                    except Exception as e:
                        logger.error(f"Streaming error: {str(e)}")
                        error_data = json.dumps({"error": {"message": str(e), "type": "streaming_error"}})
                        yield f"data: {error_data}\n\n"
                        yield "data: [DONE]\n\n"
                
                return StreamingResponse(stream_response(), media_type="text/event-stream")
            else:
                response = litellm.completion(**completion_kwargs)
                return JSONResponse(content=response.model_dump())
                
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            status_code = getattr(e, "status_code", 500)
            if not isinstance(status_code, int):
                 status_code = 500
            return JSONResponse(status_code=status_code, content={"detail": str(e)})

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app, config
