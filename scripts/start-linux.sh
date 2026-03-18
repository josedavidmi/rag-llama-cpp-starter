#!/usr/bin/env bash
set -euo pipefail

if [ ! -f .env ] && [ -f .env.example ]; then
  cp .env.example .env
  echo "Se ha creado .env a partir de .env.example"
fi

docker compose up --build
