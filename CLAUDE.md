# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AstroPlanAI is a multi-agent astrophotography planning system using OpenAI-compatible LLM APIs. It orchestrates specialized agents (weather, ephemeris, target selection, scheduler) to create optimal imaging session plans.

## Development Commands

### Setup
```bash
# Install dependencies
pip install -e .

# Install with development tools
pip install -e ".[dev]"

# Configure environment
cp .env.template .env
# Edit .env with your LLM endpoint and model
```

### Running Examples
```bash
# Full multi-agent planning demo (requires LLM server running)
python examples/basic_plan.py

# Tools-only demo (no LLM required)
python examples/simple_query.py

# Web UI (Streamlit)
streamlit run webapp/app.py
```

### Web UI Features
The Streamlit app (`webapp/app.py`) has three tabs:
- **Plan Session**: Full multi-agent planning with location, sky coverage (8-sector compass), date range, and equipment inputs
- **Quick Tools**: AI Target Search (SIMBAD + TargetSearchAgent), Ephemeris Calculator, Target Database Query
- **About**: System info and feature overview

Sky coverage uses an 8-sector compass (N/NE/E/SE/S/SW/W/NW) with presets and minimum altitude filtering.

### Testing
```bash
# Run test suite
pytest tests/

# Run tests with verbose output
pytest tests/ -v
```

### Code Quality
```bash
# Format code
black src/ examples/

# Check linting
ruff check src/ examples/
```

### Docker Usage

**Note**: The project connects to an external LLM server via an OpenAI-compatible API endpoint.

```bash
# Build and start all services (CLI + Web UI)
docker-compose up -d

# Start only the web UI
docker-compose up -d webapp

# View logs
docker logs -f astroplan-app  # CLI app
docker logs -f astroplan-web  # Web UI

# Execute example in CLI container
docker exec -it astroplan-app python examples/basic_plan.py

# Interactive shell in container
docker exec -it astroplan-app /bin/bash

# Development mode with hot-reload
docker-compose -f docker-compose.dev.yml up -d

# Stop all services
docker-compose down
```

**Web UI Access**: After starting, access the Streamlit web interface at http://localhost:8501

**LLM Connection**: Set `LLM_BASE_URL` in your `.env` to point at your LLM server. Containers also have `host.docker.internal` mapped for reaching the host machine.

## Architecture

### Multi-Agent Orchestration Pattern

The system uses a **coordinator pattern** with parallel and sequential execution stages:

```
CoordinatorAgent (src/astroplanai/agents/coordinator.py)
├── Phase 1: PARALLEL execution
│   ├── WeatherAgent (analyzes atmospheric conditions)
│   ├── EphemerisAgent (calculates celestial mechanics)
│   └── TargetSelectionAgent (recommends DSO targets)
└── Phase 2: SEQUENTIAL execution
    └── SchedulerAgent (synthesizes all data into final plan)
```

**Key Implementation Detail**: The coordinator runs weather, ephemeris, and target selection agents in parallel using `asyncio.gather(return_exceptions=True)`, then feeds consolidated results to the scheduler agent sequentially. `plan_session()` accepts an optional `progress_callback: Callable[[str], None]` for real-time status updates (used by the Streamlit UI).

### Agent Architecture

All agents inherit from `BaseAgent` (src/astroplanai/agents/base.py) which provides:
- OpenAI-compatible async client wrapper
- System instruction management
- Consistent generate() interface

Each specialized agent (weather.py, ephemeris.py, target_selection.py, scheduler.py, target_search.py) defines:
- Domain-specific system instructions
- Agent creation factory function (e.g., `create_weather_agent()`)

**TargetSearchAgent** (`target_search.py`) is a standalone agent used by the Quick Tools UI — not part of the coordinator pipeline. It handles natural language queries like "bright galaxies in autumn" or "M33", and works in conjunction with `SimbadSearch` to provide SIMBAD data + AI imaging recommendations.

### Tools vs Agents

**Tools** (src/astroplanai/tools/) perform deterministic calculations:
- `ephemeris_calculator.py`: AstroPy-based astronomical calculations (with result caching)
- `weather_api.py`: Open-Meteo API integration for forecasts (persistent HTTP client)
- `target_database.py`: Curated DSO database with seasonal filtering (Messier, NGC, IC, Caldwell); indexed for O(1) lookups
- `simbad_search.py`: Live queries to the SIMBAD astronomical database (persistent HTTP client)

**Agents** use LLMs to analyze and synthesize tool outputs into actionable recommendations.

### Configuration Management

Configuration uses Pydantic models (src/astroplanai/config.py):
- `LLMConfig`: LLM endpoint, API key, model name
- `AgentConfig`: Temperature, max tokens, timeout
- `WeatherAPIConfig`: Optional API keys for weather services

Load configuration with `load_config()` which reads from `.env` file and validates required fields.

## LLM Integration

**Architecture**: This project connects to any **external OpenAI-compatible LLM server**.

**Requirements**:
- An LLM server exposing an OpenAI-compatible API (e.g., vLLM, Ollama, LM Studio, OpenAI, etc.)
- Configure connection in `.env` file

**Configuration**: Set `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` in `.env`

Legacy `VLLM_*` env var names are still supported as fallback aliases.

The OpenAI Python SDK (openai>=1.12.0) is used to communicate via the `/v1/chat/completions` endpoint.

## Important Implementation Notes

### Lazy Agent Loading
Agents in the coordinator are lazy-loaded via properties (coordinator.py:53-87) to avoid unnecessary initialization overhead.

### Async/Await Pattern
All agent interactions use async/await. The coordinator's `plan_session()` method is the main entry point. The Streamlit app uses `nest_asyncio` to safely run async code within Streamlit's event loop via the `run_async()` helper.

### Date Handling
- Input dates are ISO format strings: "YYYY-MM-DD"
- Internal calculations use `datetime.fromisoformat()`
- AstroPy requires `EarthLocation` objects for ephemeris calculations

### Target Database Structure
Targets in `target_database.py` have fields:
- `name`: Catalog designation (e.g., "M31")
- `common_name`: Human-readable name (e.g., "Andromeda Galaxy")
- `ra`, `dec`: Coordinates in degrees
- `target_type`: Enum (GALAXY, NEBULA, CLUSTER, etc.)
- `magnitude`, `size_arcmin`: Observability metrics
- `best_months`: List of optimal viewing months

The database covers Messier, NGC, IC, and Caldwell objects (~50+ targets). Query methods: `filter_by_season(month)`, `search_by_name(query)`, `filter_by_type(target_type)`. Month and type indices are built at init for O(1) lookups.

### Equipment Dict Structure
The `equipment` dict passed to `plan_session()` includes:
```python
{
    "camera": str,
    "lens": str,
    "focal_length_mm": int,
    "sensor_width_mm": float,
    "sensor_height_mm": float,
    "mount": str,
    "sky_coverage": {
        "available_sectors": List[str],  # e.g., ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        "min_altitude_deg": int,         # minimum target altitude (0-60 degrees)
    }
}
```

## Common Development Tasks

### Adding a New Agent
1. Create new file in `src/astroplanai/agents/`
2. Define system instruction string
3. Create factory function that returns `BaseAgent` instance
4. Import and integrate in `coordinator.py`

### Adding New Tools
1. Create new file in `src/astroplanai/tools/`
2. Implement as regular Python class/functions (sync or async)
3. Initialize tool in coordinator's `__init__` method
4. Call tool in agent-specific methods (e.g., `_get_weather_analysis()`)

### Modifying Agent Behavior
Edit the system instruction string in the agent's factory function. This defines the agent's role, output format, and reasoning approach.

### Testing Without LLM
Use `examples/simple_query.py` which demonstrates tools directly without LLM agents. Useful for testing core calculation logic.

## Environment Variables

Required:
- `LLM_MODEL`: Model name to use (e.g., "meta-llama/Llama-3.1-8B-Instruct")

Optional:
- `LLM_BASE_URL`: Default "http://localhost:8000/v1"
- `LLM_API_KEY`: Default "not_required_for_local"
- `AGENT_TIMEOUT_SECONDS`: Default 60
- `AGENT_TEMPERATURE`: Default 0.7
- `AGENT_MAX_TOKENS`: Default 4096
- `METEO_BLUE_API_KEY`: For premium weather API
- `OPEN_METEO_API_KEY`: Not required for free tier

Legacy aliases (backward-compatible): `VLLM_MODEL`, `VLLM_BASE_URL`, `VLLM_API_KEY`

## Code Style

- Line length: 100 characters (configured in pyproject.toml)
- Formatter: Black
- Linter: Ruff
- Target: Python 3.10+
- Use type hints where practical
- Docstrings: Google style with Args/Returns sections
