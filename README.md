# AstroPlanAI

> Multi-agent astrophotography planning system using local VLLM models

AstroPlanAI is a sophisticated multi-agent system that helps astrophotographers plan optimal imaging sessions by analyzing weather forecasts, celestial mechanics, and equipment capabilities. It demonstrates advanced agent orchestration with local LLMs via VLLM (OpenAI-compatible API) using parallel and sequential workflows.

## Features

- **Multi-Agent Architecture**: Specialized agents for weather, ephemeris, target selection, and scheduling
- **Parallel Processing**: Weather, ephemeris, and target analysis run concurrently for efficiency
- **Comprehensive Analysis**:
  - Real-time weather forecasts (cloud cover, humidity, seeing, transparency)
  - Astronomical calculations (moon phase, twilight times, target visibility)
  - Intelligent target recommendations based on season, equipment, and conditions
  - Detailed imaging schedules with specific time windows
- **Equipment-Aware**: Factors in focal length, field of view, and mount capabilities
- **Astronomy Tools**: Built on AstroPy and real weather APIs (Open-Meteo)

## Architecture

The system uses a coordinator pattern with specialized sub-agents:

```
CoordinatorAgent
├── WeatherAgent (analyzes atmospheric conditions)
├── EphemerisAgent (calculates celestial mechanics)
├── TargetSelectionAgent (recommends DSO targets)
└── SchedulerAgent (synthesizes inputs into actionable plan)
```

**Agent Flow:**
1. **Parallel Stage**: Weather + Ephemeris + Target Selection run concurrently
2. **Sequential Stage**: Scheduler receives consolidated data and generates plan
3. **Output**: Detailed imaging schedule with times, targets, and recommendations

## Installation

### Prerequisites

- Python 3.10 or higher
- A running VLLM server (local or remote)
- See [VLLM_SETUP.md](VLLM_SETUP.md) for detailed VLLM installation instructions

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd AstroPlanAI
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Configure VLLM connection:
```bash
cp .env.template .env
# Edit .env and configure your VLLM endpoint and model
```

Example `.env`:
```bash
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_API_KEY=not_required_for_local
VLLM_MODEL=meta-llama/Llama-3.1-8B-Instruct
```

**Need help setting up VLLM?** See [VLLM_SETUP.md](VLLM_SETUP.md) for a complete guide.

## Usage

### Basic Example

```python
from astroplanai.agents.coordinator import create_coordinator_agent
from astroplanai.config import load_config
import asyncio

async def main():
    config = load_config()

    coordinator = create_coordinator_agent({
        "vllm_base_url": config.vllm.base_url,
        "vllm_api_key": config.vllm.api_key,
        "vllm_model": config.vllm.model,
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
            "mount": "Equatorial with tracking",
        }
    )

    print(schedule)

asyncio.run(main())
```

### Run Example Scripts

```bash
# Web Interface (Recommended)
streamlit run webapp/app.py
# Then open http://localhost:8501 in your browser

# Or use CLI examples:
# Full planning demo
python examples/basic_plan.py

# Tools demonstration (without LLM agents)
python examples/simple_query.py
```

## Project Structure

```
AstroPlanAI/
├── src/astroplanai/
│   ├── agents/              # Agent definitions
│   │   ├── coordinator.py   # Main orchestration agent
│   │   ├── weather.py       # Weather analysis agent
│   │   ├── ephemeris.py     # Celestial calculations agent
│   │   ├── target_selection.py  # Target recommendation agent
│   │   └── scheduler.py     # Schedule generation agent
│   ├── tools/               # Core calculation tools
│   │   ├── weather_api.py   # Weather API integration
│   │   ├── ephemeris_calculator.py  # AstroPy calculations
│   │   └── target_database.py      # DSO target database
│   └── config.py            # Configuration management
├── webapp/                  # Streamlit web interface
│   └── app.py              # Web application
├── examples/                # CLI example scripts
├── tests/                   # Unit tests
├── pyproject.toml          # Project dependencies
└── README.md               # This file
```

## How It Works

### 1. Weather Analysis
The `WeatherAgent` fetches forecasts from Open-Meteo's astronomy API and evaluates:
- Cloud cover (total, low, mid, high altitude)
- Humidity (for dew point and transparency)
- Wind speed (telescope stability)
- Quality scores for each night

### 2. Ephemeris Calculations
The `EphemerisAgent` uses AstroPy to compute:
- Astronomical twilight times (18° below horizon)
- Moon phase and illumination percentage
- Target rise/set times and altitude windows
- Darkness duration for imaging

### 3. Target Selection
The `TargetSelectionAgent` recommends deep-sky objects based on:
- Seasonal visibility (best months for each target)
- Equipment field of view (size matching)
- Moon conditions (bright targets for full moon, faint for new moon)
- Altitude constraints (prioritize high-altitude targets)

### 4. Schedule Generation
The `SchedulerAgent` synthesizes all inputs to create:
- Per-night quality rankings
- Specific imaging windows (start/end times)
- Target timeline with rise/set and peak altitude
- Priority recommendations (primary, secondary, backup)

## Data Sources

- **Weather**: [Open-Meteo API](https://open-meteo.com/) (free, no API key required for basic usage)
- **Ephemeris**: [AstroPy](https://www.astropy.org/) (local calculations)
- **Targets**: Curated database of popular Messier, NGC, and IC objects

## Configuration

Edit `.env` to customize:

```bash
# Required: VLLM connection
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_API_KEY=not_required_for_local
VLLM_MODEL=meta-llama/Llama-3.1-8B-Instruct

# Optional: Agent behavior
AGENT_TIMEOUT_SECONDS=60
AGENT_TEMPERATURE=0.7
AGENT_MAX_TOKENS=4096
```

## Development

### Running Tests
```bash
pip install -e ".[dev]"
pytest tests/
```

### Code Formatting
```bash
black src/ examples/
ruff check src/ examples/
```

## Roadmap

- [ ] Add A2A (Agent-to-Agent) protocol support for distributed agents
- [ ] Integrate real-time seeing forecasts (e.g., MeteoBlue)
- [ ] Light pollution database integration (Bortle scale)
- [ ] Field of view visualization and framing suggestions
- [ ] Satellite prediction (ISS, Starlink avoidance)
- [ ] Memory system for user preferences
- [ ] Voice/chat interface for natural language queries
- [ ] Streamlit dashboard for visual planning

## Why Multi-Agent?

This problem naturally decomposes into specialized reasoning tasks:
- **Weather forecasting** requires domain knowledge of atmospheric conditions
- **Ephemeris** requires precise astronomical calculations
- **Target selection** requires contextual understanding of seasonal visibility and equipment
- **Scheduling** requires synthesizing all inputs into an optimal plan

By using separate agents, each can:
- Maintain focused expertise
- Be developed and tested independently
- Run in parallel when possible
- Be easily extended with new capabilities

This is a perfect demonstration of multi-agent orchestration with local LLMs.

## Contributing

Contributions welcome! Areas of interest:
- Additional weather API integrations
- More sophisticated target databases (e.g., SIMBAD queries)
- Equipment profile library
- Calibration frame planning
- Integration with telescope control software

## License

MIT License - see LICENSE file for details

## Acknowledgments

- LLM orchestration via [OpenAI Python SDK](https://github.com/openai/openai-python) with [VLLM](https://github.com/vllm-project/vllm)
- Astronomical calculations by [AstroPy](https://www.astropy.org/)
- Weather data from [Open-Meteo](https://open-meteo.com/)
- Inspired by the astrophotography community
