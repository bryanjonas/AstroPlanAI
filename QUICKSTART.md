# Quick Start Guide

Get AstroPlanAI running in a few minutes.

## Step 1: Start an LLM Server

AstroPlanAI works with any OpenAI-compatible API endpoint. Pick whichever option suits you:

### Ollama (easiest, no GPU required)

```bash
# Install: https://ollama.com
ollama pull llama3.1:8b
ollama serve
```

Then set in `.env`:
```bash
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=llama3.1:8b
```

### vLLM (fastest, GPU recommended)

```bash
docker run --runtime nvidia --gpus all \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -p 8000:8000 --ipc=host \
    vllm/vllm-openai:latest \
    --model meta-llama/Llama-3.1-8B-Instruct \
    --dtype auto --api-key not_required
```

Then set in `.env`:
```bash
LLM_BASE_URL=http://localhost:8000/v1
LLM_API_KEY=not_required
LLM_MODEL=meta-llama/Llama-3.1-8B-Instruct
```

### LM Studio (GUI app, no GPU required)

1. Download [LM Studio](https://lmstudio.ai) and load a model
2. Click **Start Server** (default port: 1234)

Then set in `.env`:
```bash
LLM_BASE_URL=http://localhost:1234/v1
LLM_API_KEY=lm-studio
LLM_MODEL=<model name shown in LM Studio's API tab>
```

### OpenAI (no local hardware)

```bash
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-key
LLM_MODEL=gpt-4o-mini
```

---

## Step 2: Install AstroPlanAI

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -e .

cp .env.template .env
# Edit .env with your LLM settings (see Step 1)
```

---

## Step 3: Run

### Web Interface (recommended)

```bash
streamlit run webapp/app.py
# Open http://localhost:8501
```

### CLI Demo

```bash
# Full multi-agent planning (requires LLM)
python examples/basic_plan.py

# Test tools only — no LLM needed
python examples/simple_query.py
```

---

## What You'll Get

A planning session produces:

- **Night rankings**: Quality scores (0–100) for each night in your date range
- **Weather breakdown**: Cloud cover, humidity, wind per night
- **Moon information**: Phase, illumination %, interference assessment
- **Target recommendations**: 3–5 deep-sky objects ranked by suitability
- **Imaging timeline**: Specific windows for each target's optimal altitude
- **Practical advice**: Setup tips, backup targets, equipment-specific notes

### Quality Score Reference

| Score | Conditions |
|-------|-----------|
| 90–100 | Excellent — clear, low humidity, calm |
| 70–89  | Good — mostly clear, usable |
| 50–69  | Fair — some clouds, borderline |
| < 50   | Poor — not recommended |

### Moon Phase Reference

| Illumination | Impact |
|-------------|--------|
| 0–20% | New moon — best for faint galaxies and nebulae |
| 20–60% | Crescent — bright targets and emission nebulae |
| 60–100% | Bright moon — planets and bright targets only |

---

## Customize for Your Location

Edit `examples/basic_plan.py`:

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
    "sensor_width_mm": SENSOR_WIDTH,
    "sensor_height_mm": SENSOR_HEIGHT,
    "mount": "Equatorial with tracking",
}
```

---

## Troubleshooting

### "LLM_MODEL not found"
- Confirm `.env` exists in the project root and contains `LLM_MODEL=...`
- Make sure the line isn't commented out

### "Connection refused"
- Verify your LLM server is running
- Check the port in `LLM_BASE_URL` matches the actual server port

### Slow responses
- Smaller models (8B) are significantly faster than larger ones
- For vLLM/GPU setups, check `nvidia-smi` for GPU utilization

### Context length errors
- Lower `AGENT_MAX_TOKENS` in `.env` to `1024` or `1536`
- Reduce the date range to 3–5 days

### Weather API errors
- Open-Meteo is free and requires no API key
- Check your internet connection and that lat/lon values are valid

---

## Next Steps

- **Web interface**: `streamlit run webapp/app.py` for a full GUI
- **Docker**: See [DOCKER.md](DOCKER.md) for containerized deployment
- **Extend agents**: Edit system instructions in `src/astroplanai/agents/` to change behavior
- **Add targets**: Extend `target_database.py` with your favorite DSOs
- **Full docs**: See [README.md](README.md)

Happy imaging! 🌌🔭
