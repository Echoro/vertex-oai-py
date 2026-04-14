import yaml
from pathlib import Path
from pydantic import BaseModel

class VertexSettings(BaseModel):
    project: str
    location: str

class ServerSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    log_to_file: bool = True
    max_log_lines: int = 10000

class Config(BaseModel):
    vertex_settings: VertexSettings
    server: ServerSettings

def load_config(config_path: str = "config.yaml") -> Config:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file {config_path} not found")
    
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    
    return Config(**data)
