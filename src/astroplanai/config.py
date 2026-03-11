"""Configuration management for AstroPlanAI."""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os


class AgentConfig(BaseModel):
    """Configuration for LLM agents."""

    timeout_seconds: int = Field(default=60)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096)


class LLMConfig(BaseModel):
    """Configuration for LLM endpoint (OpenAI-compatible API)."""

    base_url: str = Field(default="http://localhost:8000/v1")
    api_key: str = Field(default="not_required_for_local")
    model: str = Field(...)


class WeatherAPIConfig(BaseModel):
    """Configuration for weather API services."""

    meteo_blue_api_key: Optional[str] = Field(default=None)
    open_meteo_api_key: Optional[str] = Field(default=None)


class Config(BaseModel):
    """Main configuration for AstroPlanAI."""

    agent: AgentConfig = Field(default_factory=AgentConfig)
    llm: LLMConfig
    weather_api: WeatherAPIConfig = Field(default_factory=WeatherAPIConfig)


def load_config(env_path: Optional[Path] = None) -> Config:
    """
    Load configuration from environment variables.

    Args:
        env_path: Optional path to .env file. If None, searches in current and parent dirs.

    Returns:
        Config object with loaded settings.

    Raises:
        ValueError: If required environment variables are missing.
    """
    if env_path:
        load_dotenv(env_path)
    else:
        load_dotenv()

    # Support both new LLM_* names and legacy VLLM_* names
    llm_model = os.getenv("LLM_MODEL") or os.getenv("VLLM_MODEL")
    if not llm_model:
        raise ValueError(
            "LLM_MODEL not found in environment. "
            "Please copy .env.template to .env and configure your LLM settings."
        )

    llm_base_url = (
        os.getenv("LLM_BASE_URL")
        or os.getenv("VLLM_BASE_URL")
        or "http://localhost:8000/v1"
    )
    llm_api_key = (
        os.getenv("LLM_API_KEY")
        or os.getenv("VLLM_API_KEY")
        or "not_required_for_local"
    )

    return Config(
        agent=AgentConfig(
            timeout_seconds=int(os.getenv("AGENT_TIMEOUT_SECONDS", "60")),
            temperature=float(os.getenv("AGENT_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("AGENT_MAX_TOKENS", "4096")),
        ),
        llm=LLMConfig(
            base_url=llm_base_url,
            api_key=llm_api_key,
            model=llm_model,
        ),
        weather_api=WeatherAPIConfig(
            meteo_blue_api_key=os.getenv("METEO_BLUE_API_KEY"),
            open_meteo_api_key=os.getenv("OPEN_METEO_API_KEY"),
        ),
    )
