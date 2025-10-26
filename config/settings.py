from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3.1:8b"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    
    vector_db_type: str = "chroma"
    chroma_persist_dir: str = "./data/chroma_db"
    
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    max_chunk_size: int = 512
    chunk_overlap: int = 50
    top_k_retrieval: int = 5
    
    max_search_results: int = 20
    scraping_delay: int = 2

    llm_request_timeout: float = 300.0

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

settings = Settings()