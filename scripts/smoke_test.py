#!/usr/bin/env python3
"""Smoke test: runs without API key (mock); uses live Nemotron if NEBIUS_API_KEY is set.

Usage (from repo root):
  python scripts/smoke_test.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

from agent import explain_risk
from tajmed_agent.config import nebius_api_key, nebius_model
from tajmed_agent.risk import mqea_available, predict_risk, summary_for_llm


def main() -> int:
    demo = ROOT / "demo_data" / "patient_demo.csv"
    assert demo.exists(), f"missing {demo}"
    df = pd.read_csv(demo)
    print(f"[ok] loaded demo: {demo.name} rows={len(df)}")

    result = predict_risk(df)
    print(
        f"[ok] risk backend={result.backend} mqea_available={mqea_available()} "
        f"latest={result.latest_risk:.4f} alert={result.latest_alert} "
        f"threshold={result.threshold:.4f} hours={len(result.hours)}"
    )
    assert 0.0 <= result.latest_risk <= 1.0
    assert len(result.hours) == len(df)
    summary = summary_for_llm(result)
    assert "top_factors" in summary
    print(f"[ok] summary factors={len(summary['top_factors'])}")

    mock = explain_risk(result, mock=True)
    assert mock["mocked"] is True
    assert mock["ru"] and mock["tj"]
    print("[ok] mock explanation RU/TJ present")

    key = nebius_api_key()
    if not key:
        print("[skip] NEBIUS_API_KEY not set — live Nemotron call skipped")
        print("SMOKE_OK")
        return 0

    print(f"[..] calling Nemotron model={nebius_model()!r}")
    live = explain_risk(result, mock=False)
    assert live["mocked"] is False
    assert live.get("ru") or live.get("raw")
    print(f"[ok] live explanation chars_ru={len(live.get('ru') or '')} chars_tj={len(live.get('tj') or '')}")
    print("SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
