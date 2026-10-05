"""Environment / Nebius Token Factory settings."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

# Default matches Nebius Token Factory docs; override via NEBIUS_MODEL
DEFAULT_BASE_URL = "https://api.tokenfactory.nebius.com/v1/"
DEFAULT_MODEL = "nvidia/Nemotron-3_5-Lightning"

# Sibling MQEA-EW checkout (do not retrain)
MQEA_EW_ROOT = Path(os.environ.get("MQEA_EW_ROOT", "/workspace/mqea_ew"))


def nebius_api_key() -> str | None:
    key = os.environ.get("NEBIUS_API_KEY", "").strip()
    return key or None


def nebius_base_url() -> str:
    return os.environ.get("NEBIUS_BASE_URL", DEFAULT_BASE_URL).rstrip("/") + "/"


def nebius_model() -> str:
    return os.environ.get("NEBIUS_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
