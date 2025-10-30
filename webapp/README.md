# AstroPlanAI Web Interface

Streamlit-based web application for astrophotography session planning.

## Features

### Plan Session Tab
- **Location Input**: Select from preset dark sky sites or enter custom coordinates
- **Date Range**: Pick start and end dates for your imaging session
- **Equipment Configuration**: Camera, lens/telescope, focal length, sensor size, mount type
- **Generate Plan**: Click to create a detailed imaging schedule
- **Export**: Download the generated plan as a text file

### Quick Tools Tab
- **Ephemeris Calculator**: Calculate twilight times, moon phase, and more for any date/location
- **Target Database**: Search for deep-sky objects by season, name, or type

### About Tab
- System configuration and model information
- Architecture overview
- Data sources and credits

## Running Locally

### With Docker (Recommended)

```bash
# From project root
docker-compose up -d webapp

# Access at http://localhost:8501
```

### Without Docker

```bash
# From project root
pip install -e .
streamlit run webapp/app.py
```

## Development

### Hot Reload

In development mode, Streamlit automatically reloads when you save changes:

```bash
# Use development compose file
docker-compose -f docker-compose.dev.yml up -d webapp
```

### File Structure

```
webapp/
├── app.py          # Main Streamlit application
└── README.md       # This file
```

## Configuration

The web app reads configuration from environment variables (`.env` file):

- `VLLM_BASE_URL`: VLLM endpoint
- `VLLM_API_KEY`: API key if required
- `VLLM_MODEL`: Model name
- `AGENT_TEMPERATURE`: LLM sampling temperature
- `AGENT_MAX_TOKENS`: Maximum tokens per response

## UI Components

### Location Presets

Includes popular dark sky locations:
- Santa Fe, NM
- Cherry Springs State Park, PA
- Mauna Kea, HI
- Big Bend National Park, TX
- Death Valley, CA
- Jasper National Park, Canada

### Caching

The coordinator agent is cached using `@st.cache_resource` to avoid re-initializing the OpenAI client on every interaction.

## Customization

To add more location presets, edit the `PRESET_LOCATIONS` dictionary in `app.py`:

```python
PRESET_LOCATIONS = {
    "My Dark Sky Site": {"lat": 0.0, "lon": 0.0, "elevation": 0},
    # ...
}
```

## Troubleshooting

### "Configuration error: VLLM_MODEL not found"
- Ensure `.env` file exists in project root
- Set `VLLM_MODEL` to match your VLLM server's loaded model

### "Connection refused" errors
- Verify VLLM server is running: `curl http://localhost:8000/health`
- Check `VLLM_BASE_URL` in `.env`
- For Docker: ensure `extra_hosts` is configured for `host.docker.internal`

### Slow response times
- Planning sessions may take 30-60 seconds depending on VLLM model size
- Use smaller models (8B) for faster responses
- Check GPU utilization with `nvidia-smi`

## Browser Compatibility

Tested with:
- Chrome/Chromium
- Firefox
- Safari
- Edge

## Port Configuration

Default port is 8501. To change:

```bash
streamlit run webapp/app.py --server.port=YOUR_PORT
```

Or set in Dockerfile.webapp:
```dockerfile
ENV STREAMLIT_SERVER_PORT=YOUR_PORT
EXPOSE YOUR_PORT
```
