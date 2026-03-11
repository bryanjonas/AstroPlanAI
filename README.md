# AstroPlanAI

> Multi-agent astrophotography planning system powered by any OpenAI-compatible LLM

AstroPlanAI orchestrates specialized AI agents to create optimal imaging session plans by analyzing weather forecasts, celestial mechanics, and equipment capabilities.

## Features

- **Multi-Agent Architecture**: Specialized agents for weather, ephemeris, target selection, and scheduling run in parallel
- **AI Target Search**: Natural language search across SIMBAD's astronomical database with AI imaging recommendations
- **Sky Coverage Constraints**: Account for obstructions (trees, buildings) using an 8-sector compass with altitude filtering
- **Real-Time Data**: Live weather forecasts (Open-Meteo) and astronomical calculations (AstroPy)
- **Equipment-Aware**: Factors in focal length, field of view, sensor size, and mount capabilities
- **Works With Any LLM**: vLLM, Ollama, LM Studio, OpenAI, or any OpenAI-compatible endpoint

## Architecture

```
CoordinatorAgent
├── WeatherAgent        — analyzes atmospheric conditions (parallel)
├── EphemerisAgent      — calculates twilight, moon phase, darkness window (parallel)
├── TargetSelectionAgent — recommends DSO targets by season & equipment (parallel)
└── SchedulerAgent      — synthesizes all inputs into an actionable plan (sequential)
```

## Quick Start

### 1. Install dependencies

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
```

### 2. Configure your LLM endpoint

```bash
cp .env.template .env
```

Edit `.env`:

```bash
LLM_BASE_URL=http://localhost:8000/v1   # your LLM server
LLM_API_KEY=not_required                # or your API key
LLM_MODEL=your-model-name               # e.g. meta-llama/Llama-3.1-8B-Instruct
```

AstroPlanAI works with **any OpenAI-compatible API**:
- [vLLM](https://github.com/vllm-project/vllm) — fastest local inference (GPU recommended)
- [Ollama](https://ollama.com) — easy local setup, no GPU required
- [LM Studio](https://lmstudio.ai) — GUI-based desktop app
- OpenAI, Groq, Together AI, Fireworks, or any other compatible provider

### 3. Run

```bash
# Web interface (recommended)
streamlit run webapp/app.py
# Open http://localhost:8501

# CLI example
python examples/basic_plan.py

# Test tools without an LLM
python examples/simple_query.py
```

## Web Interface

The Streamlit app at `webapp/app.py` has three tabs:

### Plan Session
- Location picker (presets + custom coordinates)
- 8-sector sky coverage compass (mark obstructed directions)
- Minimum altitude slider
- Date range selector
- Equipment configuration (camera, lens, focal length, sensor size, mount)
- Generates a complete imaging schedule with per-night rankings

### Quick Tools
- **AI Target Search** — query SIMBAD by name or natural language; get field-of-view matching and AI imaging tips
- **Ephemeris Calculator** — twilight times, moon phase, and darkness window for any location/date
- **Target Database** — browse the built-in DSO catalog by season, name, or object type

### About
- System info, architecture overview, data sources

## API Usage

```python
from astroplanai.agents.coordinator import create_coordinator_agent
from astroplanai.config import load_config
import asyncio

async def main():
    config = load_config()

    coordinator = create_coordinator_agent({
        "llm_base_url": config.llm.base_url,
        "llm_api_key": config.llm.api_key,
        "llm_model": config.llm.model,
        "temperature": config.agent.temperature,
        "max_tokens": config.agent.max_tokens,
    })

    schedule = await coordinator.plan_session(
        location={"lat": 35.6870, "lon": -105.9378, "elevation": 2134},
        date_range={"start": "2025-11-10", "end": "2025-11-17"},
        equipment={
            "camera": "Canon R6",
            "lens": "400mm f/5.6",
            "focal_length_mm": 400,
            "sensor_width_mm": 36,
            "sensor_height_mm": 24,
            "mount": "Equatorial with tracking",
            "sky_coverage": {
                "available_sectors": ["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
                "min_altitude_deg": 30,
            },
        }
    )
    print(schedule)

asyncio.run(main())
```

## Project Structure

```
AstroPlanAI/
├── src/astroplanai/
│   ├── agents/
│   │   ├── coordinator.py       # Main orchestration
│   │   ├── weather.py
│   │   ├── ephemeris.py
│   │   ├── target_selection.py
│   │   ├── target_search.py     # Standalone AI target search
│   │   └── scheduler.py
│   ├── tools/
│   │   ├── weather_api.py       # Open-Meteo integration
│   │   ├── ephemeris_calculator.py  # AstroPy calculations
│   │   ├── target_database.py   # Curated DSO database
│   │   └── simbad_search.py     # Live SIMBAD queries
│   └── config.py
├── webapp/
│   └── app.py                   # Streamlit web interface
├── examples/
│   ├── basic_plan.py            # Full multi-agent demo
│   └── simple_query.py          # Tools-only demo (no LLM)
├── tests/
└── pyproject.toml
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_MODEL` | Yes | — | Model name (must match your server) |
| `LLM_BASE_URL` | No | `http://localhost:8000/v1` | LLM API endpoint |
| `LLM_API_KEY` | No | `not_required_for_local` | API key |
| `AGENT_TIMEOUT_SECONDS` | No | `60` | Per-agent timeout |
| `AGENT_TEMPERATURE` | No | `0.7` | LLM sampling temperature |
| `AGENT_MAX_TOKENS` | No | `2048` | Max tokens per response |

Legacy `VLLM_*` variable names are still accepted as fallback aliases.

## Docker

See [DOCKER.md](DOCKER.md) for containerized deployment.

## Development

```bash
pip install -e ".[dev]"
pytest tests/
black src/ examples/
ruff check src/ examples/
```

## Data Sources

- **Weather**: [Open-Meteo API](https://open-meteo.com/) — free, no API key required
- **Ephemeris**: [AstroPy](https://www.astropy.org/) — local calculations
- **Object Search**: [SIMBAD](https://simbad.u-strasbg.fr/) — astronomical database
- **Target Catalog**: Curated Messier, NGC, IC, and Caldwell objects

## License

MIT License — see LICENSE file for details
