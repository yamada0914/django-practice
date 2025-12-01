#!/bin/bash
set -euo pipefail

PROJECT_ROOT="/Users/wataru_ikeda/Documents/django-practice"
VENV_PATH="$PROJECT_ROOT/venv"

if [ ! -d "$VENV_PATH" ]; then
  echo "venv が見つかりません: $VENV_PATH"
  echo "python3 -m venv venv で仮想環境を作成してください"
  exit 1
fi

source "$VENV_PATH/bin/activate"
cd "$PROJECT_ROOT"

python -m pip install --upgrade pip >/dev/null
pip install -r requirements.txt >/dev/null

export DJANGO_SETTINGS_MODULE="config.settings"
pytest "$@"

