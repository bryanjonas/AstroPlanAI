# Docker Deployment Guide

AstroPlanAI runs as a fully containerized application that connects to an external VLLM server on your host machine.

## Architecture

```
┌──────────────────────────────────────────────┐
│   Host Machine                               │
│                                              │
│  ┌──────────────────┐                        │
│  │  VLLM Server     │                        │
│  │  Port: 8000      │                        │
│  └────────┬─────────┘                        │
│           │                                  │
│  ┌────────▼──────────────────────────────┐   │
│  │  Docker                               │   │
│  │  ┌────────────┐   ┌────────────────┐  │   │
│  │  │ AstroPlanAI│   │  Web UI        │  │   │
│  │  │ CLI        │   │  (Streamlit)   │  │   │
│  │  │            │   │  Port: 8501    │  │   │
│  │  └────────────┘   └────────────────┘  │   │
│  └──────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
```

Both containers connect to VLLM via `host.docker.internal`, which is automatically mapped to the host machine's network.

## Prerequisites

1. **VLLM Server Running on Host**
   - Install and start VLLM on your host machine (see VLLM_SETUP.md)
   - Default endpoint: `http://localhost:8000`
   - Verify it's running: `curl http://localhost:8000/health`

2. **Docker & Docker Compose**
   - Docker Engine 20.10+
   - Docker Compose 2.0+

3. **Configuration**
   - Copy `.env.template` to `.env`
   - Set `VLLM_MODEL` to match your VLLM server's loaded model
   - `VLLM_BASE_URL` defaults to `http://host.docker.internal:8000/v1`

## Quick Start

### 1. Start VLLM on Host

```bash
# Example: Start VLLM with Docker on host
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

### 2. Configure Environment

```bash
cp .env.template .env
nano .env  # Set VLLM_MODEL to match your VLLM server
```

Example `.env`:
```bash
VLLM_BASE_URL=http://host.docker.internal:8000/v1
VLLM_API_KEY=not_required
VLLM_MODEL=meta-llama/Llama-3.1-8B-Instruct
```

### 3. Start AstroPlanAI Containers

```bash
# Start all services (CLI + Web UI)
docker-compose up -d

# Or start only the web UI
docker-compose up -d webapp
```

The system will start two containers:
- **CLI Container** (`astroplan-app`): Command-line interface and examples
- **Web UI Container** (`astroplan-web`): Streamlit web interface on port 8501

### 4. Access the Web Interface

Open your browser and navigate to:
```
http://localhost:8501
```

You should see the AstroPlanAI web interface with:
- **Plan Session** tab: Interactive form for creating imaging plans
- **Quick Tools** tab: Ephemeris calculator and target database queries
- **About** tab: System information and documentation

### 5. Or Use CLI Examples

```bash
# Execute example in CLI container
docker exec -it astroplan-app python examples/basic_plan.py

# Or open interactive shell
docker exec -it astroplan-app /bin/bash
```

## Development Mode

For development with hot-reload:

```bash
docker-compose -f docker-compose.dev.yml up -d
```

This mounts source code as read-only volumes, so changes on host are immediately reflected in the container.

## Troubleshooting

### Container can't reach VLLM

**Symptoms**: Container logs show "Could not connect to external VLLM server"

**Solutions**:
1. Verify VLLM is running: `curl http://localhost:8000/health`
2. Check VLLM is listening on correct port (default: 8000)
3. On Linux, ensure `extra_hosts` is configured (already set in docker-compose.yml)
4. Try using host IP instead: `VLLM_BASE_URL=http://192.168.1.x:8000/v1`

### Model mismatch errors

**Symptoms**: API errors about unknown model

**Solutions**:
1. Check loaded model: `curl http://localhost:8000/v1/models`
2. Update `VLLM_MODEL` in `.env` to match exactly
3. Restart container: `docker-compose restart`

### Container exits immediately

**Symptoms**: Container starts but exits right away

**Solutions**:
1. Check logs: `docker logs astroplan-app`
2. Verify `.env` file exists and has `VLLM_MODEL` set
3. Try starting manually: `docker-compose up` (without `-d`)

## Container Management

```bash
# View logs
docker logs -f astroplan-app

# Restart container
docker-compose restart

# Stop container
docker-compose down

# Rebuild after code changes
docker-compose build
docker-compose up -d

# Remove everything (including volumes)
docker-compose down -v
```

## Workspace Directory

The `/workspace` directory is mounted from `./workspace` on host:

```bash
# Host: Create script in workspace
echo 'print("Hello from workspace")' > workspace/test.py

# Container: Run it
docker exec -it astroplan-app python /workspace/test.py
```

This is useful for:
- Custom scripts
- Output files (plans, logs)
- Temporary data

## Network Configuration

### Default (host.docker.internal)

Works out-of-box on:
- macOS
- Windows
- Linux (via `extra_hosts` in docker-compose.yml)

### Alternative: Host Network Mode

For direct host network access (Linux only):

```yaml
# Add to docker-compose.yml
services:
  astroplanai:
    network_mode: "host"
```

Then use `VLLM_BASE_URL=http://localhost:8000/v1`

⚠️ **Caveat**: `host` network mode doesn't work on macOS/Windows.

### Remote VLLM

To connect to VLLM on another machine:

```bash
VLLM_BASE_URL=http://192.168.1.100:8000/v1
```

## Environment Variables

See `.env.template` for full list. Key variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `VLLM_BASE_URL` | VLLM endpoint URL | `http://host.docker.internal:8000/v1` |
| `VLLM_API_KEY` | API key (if auth enabled) | `not_required` |
| `VLLM_MODEL` | Model name loaded in VLLM | **(required)** |
| `AGENT_TEMPERATURE` | LLM temperature | `0.7` |
| `AGENT_MAX_TOKENS` | Max tokens per response | `4096` |

## Production Deployment

For production use:

1. **Use specific image tags**
   ```yaml
   services:
     astroplanai:
       image: astroplanai:1.0.0
   ```

2. **Set resource limits**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 4G
   ```

3. **Use secrets for API keys**
   ```yaml
   secrets:
     vllm_api_key:
       file: ./secrets/vllm_api_key.txt
   ```

4. **Add health checks**
   ```yaml
   healthcheck:
     test: ["CMD", "python", "-c", "import astroplanai"]
     interval: 30s
     timeout: 10s
     retries: 3
   ```

5. **Use restart policies**
   ```yaml
   restart: unless-stopped
   ```

## Next Steps

- See [QUICKSTART.md](QUICKSTART.md) for usage examples
- See [VLLM_SETUP.md](VLLM_SETUP.md) for VLLM installation
- See [CLAUDE.md](CLAUDE.md) for development guidelines
