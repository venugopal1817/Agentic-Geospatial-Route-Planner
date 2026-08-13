import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "Agentic Geospatial Route Planner"
    llm_provider: str = os.getenv("LLM_PROVIDER", "local")
    llm_model: str = os.getenv("LLM_MODEL", "local-fallback")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")


settings = Settings()
