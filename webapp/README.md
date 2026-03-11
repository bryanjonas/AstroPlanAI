# AstroPlanAI Web Interface

Streamlit-based web application for astrophotography session planning.

## Running Locally

### Without Docker

```bash
# From project root
pip install -e .
streamlit run webapp/app.py
# Open http://localhost:8501
```

### With Docker

```bash
docker-compose up -d webapp
# Open http://localhost:8501
```

## Tabs

### Plan Session

Configure your imaging session and generate a multi-agent plan:

- **Location** — select from preset dark sky sites or enter custom coordinates
- **Sky Coverage** — 8-sector compass (N/NE/E/SE/S/SW/W/NW); uncheck obstructed directions (trees, buildings)
- **Minimum Altitude** — filter out targets below a set altitude (reduces atmospheric effects)
- **Date Range** — start and end dates for the session
- **Equipment** — camera, lens/telescope, focal length, sensor dimensions, mount type
- **Generate Plan** — runs weather, ephemeris, and target agents in parallel, then synthesizes a schedule
- **Download** — export the generated plan as a text file

### Quick Tools

#### AI Target Search
- Enter an object name (`M33`, `NGC 7000`) or natural language query (`bright galaxies for autumn`)
- Searches SIMBAD for exact matches; results are cached for 1 hour
- Calculates field-of-view fit for your equipment
- Gets AI imaging recommendations (exposure, filters, composition tips)
- Falls back to AI suggestions if SIMBAD doesn't find the object

#### Ephemeris Calculator
- Enter location and date to get twilight times and moon information
- Results are cached — repeat queries for the same location/date are instant

#### Target Database Query
- Browse the built-in DSO catalog by season, name, or object type
- Covers Messier, NGC, IC, and Caldwell objects

### About
- System configuration (model, endpoint, temperature, max tokens)
- Architecture overview
- Data source credits

## Configuration

The app reads from environment variables (`.env` file in project root):

| Variable | Description |
|----------|-------------|
| `LLM_BASE_URL` | LLM API endpoint (any OpenAI-compatible server) |
| `LLM_API_KEY` | API key (use `not_required` for local servers) |
| `LLM_MODEL` | Model name — must match what your server reports |
| `AGENT_TEMPERATURE` | LLM sampling temperature (default `0.7`) |
| `AGENT_MAX_TOKENS` | Max tokens per agent response (default `2048`) |

## Caching

The app uses Streamlit's caching to avoid redundant work:

- `@st.cache_resource` — `TargetDatabase`, `EphemerisCalculator`, `SimbadSearch`, and the coordinator agent are created once and reused across all interactions
- `@st.cache_data(ttl=3600)` — SIMBAD search results are cached for 1 hour per query

## Adding Location Presets

Edit `PRESET_LOCATIONS` in `app.py`:

```python
PRESET_LOCATIONS = {
    "My Dark Sky Site": {"lat": 0.0, "lon": 0.0, "elevation": 0},
    # ...
}
```

## Troubleshooting

### "Configuration error: LLM_MODEL not found"
- Ensure `.env` exists in the project root with `LLM_MODEL` set
- Restart Streamlit after editing `.env`

### "Connection refused" when generating a plan
- Verify your LLM server is running
- Check `LLM_BASE_URL` in `.env` points to the correct address and port
- For Docker: use `host.docker.internal` instead of `localhost`

### Slow plan generation
- Planning sessions take 30–90 seconds depending on model size
- Use smaller models (7–8B) for faster responses
- Check GPU utilization with `nvidia-smi` if using a local GPU server

## Port Configuration

Default port is 8501. To change:

```bash
streamlit run webapp/app.py --server.port=YOUR_PORT
```
