#!/bin/bash
# View logs from containers

SERVICE=${1:-all}

if [ "$SERVICE" = "all" ]; then
    echo "Showing logs for all services..."
    docker-compose logs -f
elif [ "$SERVICE" = "vllm" ]; then
    echo "Showing VLLM logs..."
    docker-compose logs -f vllm
elif [ "$SERVICE" = "app" ]; then
    echo "Showing AstroPlanAI logs..."
    docker-compose logs -f astroplanai
else
    echo "Usage: $0 [all|vllm|app]"
    exit 1
fi
