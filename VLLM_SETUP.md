# VLLM Setup Guide

This guide shows you how to set up and run AstroPlanAI with your local VLLM server.

## Prerequisites

- Python 3.10+
- A local VLLM server running
- Or Docker installed to run VLLM

## Option 1: Using an Existing VLLM Server

If you already have VLLM running:

1. Note your VLLM server's:
   - Base URL (e.g., `http://localhost:8000/v1`)
   - Model name (e.g., `meta-llama/Llama-3.1-8B-Instruct`)
   - API key (if authentication is enabled)

2. Configure AstroPlanAI:

```bash
cp .env.template .env
```

Edit `.env`:
```bash
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_API_KEY=not_required_for_local  # Or your API key if needed
VLLM_MODEL=your-model-name
```

3. Test the connection:

```bash
# Install dependencies
pip install -e .

# Run the tools demo (doesn't require LLM)
python examples/simple_query.py

# Run the full multi-agent demo
python examples/basic_plan.py
```

## Option 2: Starting VLLM from Scratch

### Using Docker (Recommended)

This is the easiest method if you don't have VLLM installed.

```bash
# Pull and run VLLM with Llama 3.1 8B
docker run --runtime nvidia --gpus all \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -p 8000:8000 \
    --ipc=host \
    vllm/vllm-openai:latest \
    --model meta-llama/Llama-3.1-8B-Instruct \
    --dtype auto \
    --api-key not_required
```

Wait for the model to load (first time will download the model). Once you see:
```
INFO: Application startup complete.
```

Configure AstroPlanAI:
```bash
cp .env.template .env
```

Edit `.env`:
```bash
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_API_KEY=not_required
VLLM_MODEL=meta-llama/Llama-3.1-8B-Instruct
```

### Using Python VLLM Installation

If you prefer to install VLLM directly:

```bash
# Install VLLM
pip install vllm

# Start the server
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3.1-8B-Instruct \
    --dtype auto \
    --api-key not_required
```

Then configure AstroPlanAI as shown above.

## Recommended Models

For astrophotography planning, you need a capable reasoning model:

### Small Models (8B parameters)
- **meta-llama/Llama-3.1-8B-Instruct** (Recommended for most users)
- **mistralai/Mistral-7B-Instruct-v0.3**
- Fast, good reasoning, fits on consumer GPUs

### Medium Models (20-40B parameters)
- **meta-llama/Llama-3.1-70B-Instruct** (Best quality, requires more GPU)
- **Qwen/Qwen2.5-32B-Instruct**
- Better at complex analysis and scheduling

### Minimum Requirements
- GPU: 16GB VRAM for 8B models, 40GB+ for 70B models
- RAM: 32GB system RAM recommended
- Storage: 20-100GB for model weights

## Verifying Your Setup

### 1. Test VLLM Server

```bash
curl http://localhost:8000/v1/models
```

Should return JSON with your model name.

### 2. Test OpenAI Compatibility

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is 2+2?"}
    ]
  }'
```

Should return a completion.

### 3. Test AstroPlanAI

```bash
# This doesn't need the LLM (tests tools only)
python examples/simple_query.py
```

If that works:

```bash
# Full multi-agent demo (needs VLLM)
python examples/basic_plan.py
```

## Troubleshooting

### "Connection refused"
- Check VLLM is running: `curl http://localhost:8000/health`
- Verify the port: default is 8000
- Check firewall settings

### "Model not found"
- Make sure `VLLM_MODEL` in `.env` matches the model loaded in VLLM
- Check with: `curl http://localhost:8000/v1/models`

### "Out of memory"
Try:
- Use a smaller model (8B instead of 70B)
- Reduce `--max-model-len` when starting VLLM
- Use quantization: `--quantization awq` or `--load-in-8bit`

### Slow responses
- Check GPU utilization: `nvidia-smi`
- Increase `--tensor-parallel-size` for multi-GPU
- Use faster model (Llama over Qwen for speed)

### "Invalid API key"
- Set `VLLM_API_KEY=not_required` in `.env` if your VLLM doesn't use auth
- Or match the key you set with `--api-key` when starting VLLM

## Performance Tips

### For Production Use
```bash
docker run --runtime nvidia --gpus all \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -p 8000:8000 \
    --ipc=host \
    vllm/vllm-openai:latest \
    --model meta-llama/Llama-3.1-8B-Instruct \
    --dtype float16 \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.9 \
    --tensor-parallel-size 2  # If you have 2+ GPUs
```

### For Development
```bash
# Use CPU for testing (slow but works without GPU)
pip install vllm-cpu
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3.1-8B-Instruct \
    --device cpu
```

## Alternative: Use Remote VLLM

You can also point to a remote VLLM server:

```bash
VLLM_BASE_URL=https://your-vllm-server.com/v1
VLLM_API_KEY=your-api-key
VLLM_MODEL=remote-model-name
```

This works with:
- Cloud-hosted VLLM instances
- Modal, RunPod, or other inference providers
- Your own production VLLM cluster

## Next Steps

Once VLLM is running and configured:

1. Run the basic example: `python examples/basic_plan.py`
2. Customize for your location in `examples/basic_plan.py`
3. Integrate into your own scripts using the API

See `QUICKSTART.md` and `README.md` for more details.
