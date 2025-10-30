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


class VLLMConfig(BaseModel):
    """Configuration for VLLM endpoint."""

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
    vllm: VLLMConfig
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

    vllm_model = os.getenv("VLLM_MODEL")
    if not vllm_model:
        raise ValueError(
            "VLLM_MODEL not found in environment. "
            "Please copy .env.template to .env and configure your VLLM settings."
        )

    return Config(
        agent=AgentConfig(
            timeout_seconds=int(os.getenv("AGENT_TIMEOUT_SECONDS", "60")),
            temperature=float(os.getenv("AGENT_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("AGENT_MAX_TOKENS", "4096")),
        ),
        vllm=VLLMConfig(
            base_url=os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1"),
            api_key=os.getenv("VLLM_API_KEY", "not_required_for_local"),
            model=vllm_model,
        ),
        weather_api=WeatherAPIConfig(
            meteo_blue_api_key=os.getenv("METEO_BLUE_API_KEY"),
            open_meteo_api_key=os.getenv("OPEN_METEO_API_KEY"),
        ),
    )
