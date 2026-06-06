#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
URL_FILE="$DIR/.tunnel-url"

if [ -f "$URL_FILE" ]; then
  echo "Poke Assistant URL:"
  cat "$URL_FILE"
else
  echo "Tunnel is not running. Start it first: ./scripts/start.sh"
  exit 1
fi
