import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import litellm
from py_src.config import load_config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vertex-oai-py")

def create_app(config_path: str = "config.yaml"):
    config = load_config(config_path)
    
    # Set environment variables for LiteLLM
    os.environ["VERTEX_PROJECT"] = config.vertex_settings.project
    os.environ["VERTEX_LOCATION"] = config.vertex_settings.location
    
    app = FastAPI(title="Vertex OAI Python Gateway")

    @app.post("/v1/chat/completions")
    async def chat_completions(request: Request):
        try:
            body = await request.json()
            
            # Use the default model from config if not specified in request
            model = body.get("model", config.vertex_settings.model)
            if not model.startswith("vertex_ai/"):
                # If model name doesn't specify vertex_ai, we prepend it if it's not a standard OpenAI name
                # or just use the config's default if it's ambiguous.
                # LiteLLM needs "vertex_ai/<model_id>"
                if "gpt-" in model.lower():
                    # If it's a gpt- model name, we override it with our vertex model
                    model = config.vertex_settings.model
                else:
                    model = f"vertex_ai/{model}"

            messages = body.get("messages", [])
            stream = body.get("stream", False)
            
            # Pop OpenAI-specific parameters that LiteLLM might not support for Vertex
            # vertex doesn't support some openai params, litellm usually handles this but let's be safe
            completion_kwargs = {
                "model": model,
                "messages": messages,
                "stream": stream,
            }
            
            # Forward other params
            for key in ["temperature", "top_p", "n", "max_tokens", "presence_penalty", "frequency_penalty"]:
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
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app, config
