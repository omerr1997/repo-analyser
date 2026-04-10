#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"

cleanup() {
  if [[ -n "${API_PID:-}" ]]; then
    kill "$API_PID" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

if ! command -v python >/dev/null 2>&1; then
  echo "Python is required but was not found."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required but was not found."
  exit 1
fi

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "Installing frontend dependencies..."
  (cd "$FRONTEND_DIR" && npm install)
fi

echo "Starting API on http://127.0.0.1:8000 ..."
cd "$ROOT_DIR"
python -m uvicorn repo_analyser.server:app --reload &
API_PID=$!

echo "Starting frontend on http://127.0.0.1:5173 ..."
cd "$FRONTEND_DIR"
npm run dev
