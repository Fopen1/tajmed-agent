"""Environment / Nebius Token Factory settings."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

# Defaults match Nebius Token Factory public docs / model catalog (Oct 2026)
# Docs: https://docs.tokenfactory.nebius.com/api-reference/introduction
# Catalog: https://tokenfactory.nebius.com/model-catalog.md
DEFAULT_BASE_URL = "https://api.tokenfactory.nebius.com/v1/"
DEFAULT_MODEL = "nvidia/Nemotron-3_5-Lightning"

# Known public NVIDIA Nemotron IDs on Token Factory (for docs / UI hints).
# IDs are case-sensitive and must match the catalog exactly.
KNOWN_NEMOTRON_MODELS = (
    "nvidia/Nemotron-3_5-Lightning",  # 30B MoE, cheap, eu-north1 — good default
    "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",  # Nano, eu-north1
    "nvidia/nemotron-3-super-120b-a12b",  # Super 120B, us-central1
    "nvidia/Nemotron-3-Ultra-550b-a55b",  # Ultra 550B, us-central1
)

# Sibling MQEA-EW checkout (do not retrain)
MQEA_EW_ROOT = Path(os.environ.get("MQEA_EW_ROOT", "/workspace/mqea_ew"))


def nebius_api_key() -> str | None:
    key = os.environ.get("NEBIUS_API_KEY", "").strip()
    return key or None


def nebius_base_url() -> str:
    return os.environ.get("NEBIUS_BASE_URL", DEFAULT_BASE_URL).rstrip("/") + "/"


def nebius_model() -> str:
    return os.environ.get("NEBIUS_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
