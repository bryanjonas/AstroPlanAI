#!/bin/bash
# Open an interactive shell in the AstroPlanAI container

set -e

echo "Opening interactive shell in AstroPlanAI container..."
echo ""

# Check if docker-compose is running
if ! docker ps | grep -q astroplan-app; then
    echo "Error: AstroPlanAI container is not running"
    echo "Start it with: docker-compose up -d"
    exit 1
fi

docker-compose exec astroplanai /bin/bash
