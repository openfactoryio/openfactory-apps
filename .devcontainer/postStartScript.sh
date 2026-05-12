#!/bin/bash
set -e

VENV_PATH=".venv"

if [ ! -d "$VENV_PATH" ]; then
    echo "Creating virtual environment..."
    python -m venv $VENV_PATH
fi

echo "Upgrading pip..."
$VENV_PATH/bin/python -m pip install --upgrade pip

echo "Installing project (dev dependencies)..."
$VENV_PATH/bin/python -m pip install -e .[dev]
