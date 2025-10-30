# Quick Start Guide

Get AstroPlanAI running with your local VLLM server!

## Step 1: Start VLLM Server

**Don't have VLLM yet?** See [VLLM_SETUP.md](VLLM_SETUP.md) for detailed setup instructions.

**Quick start with Docker:**
```bash
docker run --runtime nvidia --gpus all \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -p 8000:8000 \
    --ipc=host \
    vllm/vllm-openai:latest \
    --model meta-llama/Llama-3.1-8B-Instruct \
    --dtype auto \
    --api-key not_required
```

Wait for "Application startup complete" message.

## Step 2: Set Up the Project

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Configure API key
cp .env.template .env
nano .env  # or use your favorite editor
```

Configure your VLLM connection in `.env`:
```bash
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_API_KEY=not_required
VLLM_MODEL=meta-llama/Llama-3.1-8B-Instruct
```

## Step 3: Run Your First Plan

### Option A: Full Multi-Agent Demo
```bash
python examples/basic_plan.py
```

This will:
- Analyze weather for Santa Fe, NM for Nov 10-17, 2025
- Calculate moon phase and twilight times
- Recommend targets suitable for a 400mm lens
- Generate a complete imaging schedule

### Option B: Test Tools Without LLM
```bash
python examples/simple_query.py
```

This demonstrates:
- Ephemeris calculations (sunset, moon phase)
- Target visibility (when M31 is highest)
- Target database queries (November targets)

## Step 4: Customize for Your Location

Edit `examples/basic_plan.py` and change:

```python
location = {
    "lat": YOUR_LATITUDE,
    "lon": YOUR_LONGITUDE,
    "elevation": YOUR_ELEVATION_METERS,
}

date_range = {
    "start": "YYYY-MM-DD",
    "end": "YYYY-MM-DD",
}

equipment = {
    "camera": "Your Camera",
    "lens": "Your Lens",
    "focal_length_mm": FOCAL_LENGTH,
    # ...
}
```

## What You'll Get

A detailed plan including:
- **Night rankings**: Which nights have the best conditions (0-100 score)
- **Weather breakdown**: Cloud cover, humidity, wind per night
- **Moon information**: Phase, illumination %, interference assessment
- **Target recommendations**: 3-5 deep-sky objects ranked by suitability
- **Imaging timeline**: Specific times for each target's optimal window
- **Practical advice**: Setup tips, backup targets, constraints

## Understanding the Output

### Weather Quality Scores
- **90-100**: Excellent (clear, low humidity, calm)
- **70-89**: Good (mostly clear, acceptable conditions)
- **50-69**: Fair (some clouds, borderline usable)
- **< 50**: Poor (not recommended for imaging)

### Moon Phases
- **0-20%**: New moon - best for faint galaxies and nebulae
- **20-60%**: Crescent - bright targets and emission nebulae OK
- **60-100%**: Bright moon - planets and bright galaxies only

### Target Priority
- **Primary**: Best target for the night (highest priority)
- **Secondary**: Good alternative if primary sets early
- **Backup**: Additional options if weather deteriorates

## Troubleshooting

### "VLLM_MODEL not found"
- Make sure you copied `.env.template` to `.env`
- Check that you configured your VLLM settings
- Ensure `.env` is in the project root directory

### "Connection refused"
- Make sure VLLM is running: `curl http://localhost:8000/health`
- Check the port in VLLM_BASE_URL matches your VLLM server
- See [VLLM_SETUP.md](VLLM_SETUP.md) for troubleshooting

### "Import Error"
- Make sure you installed: `pip install -e .`
- Check your virtual environment is activated
- Try: `pip install -r requirements.txt` as a backup

### Slow responses
- VLLM needs a GPU for good performance
- 8B models are faster than 70B models
- Check GPU usage with `nvidia-smi`
- See VLLM_SETUP.md for performance tuning

### Weather API Errors
- Open-Meteo is free and requires no API key
- Check your internet connection
- Verify latitude/longitude are valid (-90 to 90, -180 to 180)

## Next Steps

1. **Explore the code**: Check out `src/astroplanai/agents/` to see how agents work
2. **Modify agents**: Edit system instructions in agent files to change behavior
3. **Add more targets**: Extend `target_database.py` with your favorite DSOs
4. **Integrate your workflow**: Use the API in your own scripts
5. **Contribute**: Add features from the roadmap in README.md

## Learn More

- **Full documentation**: See README.md
- **VLLM setup guide**: See VLLM_SETUP.md for installation help
- **Agent architecture**: Review `coordinator.py` to see orchestration
- **Tools**: Check `tools/` directory for calculation utilities

## Need Help?

Open an issue on GitHub with:
- Your Python version (`python --version`)
- Error messages (full traceback)
- What you were trying to do
- Your location/date/equipment settings (if relevant)

Happy imaging! 🌌🔭
