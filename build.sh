#!/usr/bin/env bash
set -e

echo "==> Installing dependencies..."
pip install -r requirements.txt

echo "==> Installing Tesseract OCR (se disponivel)..."
if command -v apt-get >/dev/null 2>&1; then
  apt-get install -y tesseract-ocr tesseract-ocr-por || echo "Tesseract nao instalado — OCR desabilitado"
fi

echo "==> Running database migrations..."
alembic upgrade head

echo "==> Build complete!"
