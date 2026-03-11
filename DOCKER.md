# Docker Deployment Guide

AstroPlanAI runs as a containerized application that connects to an external LLM server.

## Architecture

```
┌──────────────────────────────────────────────┐
│   Host Machine                               │
│                                              │
│  ┌──────────────────┐                        │
│  │  LLM Server      │                        │
│  │  (any port)      │                        │
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

Both containers connect to the LLM server via `host.docker.internal`, which is automatically mapped to the host machine's network on Linux (via `extra_hosts` in docker-compose.yml) and natively on macOS/Windows.

## Prerequisites

1. **LLM Server Running on Host** — any OpenAI-compatible API (vLLM, Ollama, LM Studio, etc.)
   - Verify it's running: `curl http://localhost:8000/v1/models`
   - See [QUICKSTART.md](QUICKSTART.md) for LLM setup options

2. **Docker & Docker Compose**
   - Docker Engine 20.10+
   - Docker Compose 2.0+

3. **Configuration** — copy `.env.template` to `.env` and set your LLM details

## Quick Start

### 1. Configure Environment

```bash
cp .env.template .env
```

Edit `.env`:
```bash
LLM_BASE_URL=http://host.docker.internal:8000/v1  # reach host from container
LLM_API_KEY=not_required
LLM_MODEL=your-model-name
```

> Use `host.docker.internal` as the hostname so containers can reach your host's LLM server.

### 2. Start Services

```bash
# Start all services (CLI + Web UI)
docker-compose up -d

# Or start only the Web UI
docker-compose up -d webapp
```

### 3. Access the Web Interface

Open your browser to:
```
http://localhost:8501
```

### 4. Or Use the CLI

```bash
# Run the planning example
docker exec -it astroplan-app python examples/basic_plan.py

# Open an interactive shell
docker exec -it astroplan-app /bin/bash
```

## Development Mode

For development with hot-reload (source code changes reflected immediately):

```bash
docker-compose -f docker-compose.dev.yml up -d
```

## Container Management

```bash
# View logs
docker logs -f astroplan-web   # Web UI
docker logs -f astroplan-app   # CLI

# Restart after config change
docker-compose restart

# Rebuild after code changes
docker-compose build && docker-compose up -d

# Stop all services
docker-compose down

# Remove containers and volumes
docker-compose down -v
```

## Troubleshooting

### Container can't reach the LLM server

**Symptoms**: Errors like "Connection refused" or timeout when generating a plan.

**Solutions**:
1. Verify LLM server is running: `curl http://localhost:8000/v1/models`
2. Use `host.docker.internal` in `LLM_BASE_URL` (not `localhost`)
3. On Linux, `extra_hosts: host.docker.internal:host-gateway` is already set in docker-compose.yml
4. Alternatively, use the host's LAN IP: `LLM_BASE_URL=http://192.168.1.x:8000/v1`

### Model mismatch errors

**Symptoms**: API errors about unknown model name.

**Solutions**:
1. Check which model is loaded: `curl http://localhost:8000/v1/models`
2. Update `LLM_MODEL` in `.env` to match exactly
3. Restart: `docker-compose restart`

### Container exits immediately

**Symptoms**: Container starts but exits right away.

**Solutions**:
1. Check logs: `docker logs astroplan-app`
2. Confirm `.env` exists and has `LLM_MODEL` set
3. Start without `-d` to see output: `docker-compose up`

## Workspace Directory

`./workspace` on the host is mounted at `/workspace` in the CLI container:

```bash
# Create a custom script on the host
echo 'print("Hello!")' > workspace/test.py

# Run it inside the container
docker exec -it astroplan-app python /workspace/test.py
```

Use this for custom scripts, output files, and temporary data.

## Network Configuration

### Default: host.docker.internal

Works on macOS, Windows, and Linux (via `extra_hosts` in docker-compose.yml). No changes needed.

### Alternative: Host Network Mode (Linux only)

```yaml
# In docker-compose.yml
services:
  webapp:
    network_mode: "host"
```

Then use `LLM_BASE_URL=http://localhost:8000/v1`. Note: not supported on macOS/Windows.

### Remote LLM Server

To connect to an LLM server on another machine:

```bash
LLM_BASE_URL=http://192.168.1.100:8000/v1
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_BASE_URL` | No | `http://localhost:8000/v1` | LLM API endpoint |
| `LLM_API_KEY` | No | `not_required` | API key |
| `LLM_MODEL` | **Yes** | — | Model name (must match server) |
| `AGENT_TEMPERATURE` | No | `0.7` | LLM sampling temperature |
| `AGENT_MAX_TOKENS` | No | `2048` | Max tokens per response |
| `AGENT_TIMEOUT_SECONDS` | No | `60` | Per-agent timeout |

## Production Deployment

```yaml
# docker-compose.yml additions for production
services:
  webapp:
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
    healthcheck:
      test: ["CMD", "python", "-c", "import astroplanai"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Next Steps

- [QUICKSTART.md](QUICKSTART.md) — LLM setup options and usage examples
- [README.md](README.md) — full documentation
