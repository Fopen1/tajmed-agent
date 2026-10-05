"""Risk scoring: thin adapter over MQEA-EW predict API, or a vitals stub.

MQEA-EW usage pattern (from /workspace/mqea_ew):
    from mqea_ew import predict
    out = predict(patient_df, explain=True, top_k=5)
    # columns: hour, risk (0..1), alert (bool), factors (list[dict])

We never retrain. If the package / artifacts are unavailable, we fall back to a
transparent heuristic with a clear TODO.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .config import MQEA_EW_ROOT

# Stub threshold (aligned roughly with MQEA-EW demo scale)
STUB_THRESHOLD = 0.35


@dataclass
class RiskResult:
    """Normalized prediction for the UI / agent."""

    hours: list[float]
    risks: list[float]
    alerts: list[bool]
    factors_per_hour: list[list[dict[str, Any]]]
    threshold: float
    backend: str  # "mqea_ew" | "stub"
    latest_risk: float
    latest_alert: bool
    latest_factors: list[dict[str, Any]]


def _try_import_mqea():
    """Import mqea_ew from sibling path without installing as a package."""
    root = Path(MQEA_EW_ROOT)
    art = root / "mqea_ew" / "artifacts" / "model.txt"
    if not art.exists():
        return None
    pkg_parent = str(root)
    if pkg_parent not in sys.path:
        sys.path.insert(0, pkg_parent)
    try:
        from mqea_ew import load_model, predict  # type: ignore

        return load_model, predict
    except Exception:
        return None


def mqea_available() -> bool:
    return _try_import_mqea() is not None


def _stub_score_row(row: pd.Series) -> tuple[float, list[dict[str, Any]]]:
    """Simple non-clinical heuristic from common vitals.

    TODO: Replace with MQEA-EW (or a clinically validated model) when artifacts
    are available. This stub exists only so the UI/agent run offline.
    """
    factors: list[dict[str, Any]] = []
    score = 0.05

    def add(name: str, value, contrib: float, text: str, effect: str):
        nonlocal score
        score += contrib
        factors.append(
            {
                "variable": name,
                "name_ru": name,
                "contribution": contrib,
                "effect": effect,
                "value": value,
                "text": text,
            }
        )

    hr = row.get("HR", np.nan)
    if pd.notna(hr):
        if hr >= 120:
            add("HR", float(hr), 0.22, f"ЧСС: {hr:.0f} уд/мин (высокая) — повышает риск", "повышает риск")
        elif hr >= 100:
            add("HR", float(hr), 0.12, f"ЧСС: {hr:.0f} уд/мин (умеренно высокая) — повышает риск", "повышает риск")
        elif hr < 50:
            add("HR", float(hr), 0.15, f"ЧСС: {hr:.0f} уд/мин (низкая) — повышает риск", "повышает риск")

    o2 = row.get("O2Sat", np.nan)
    if pd.notna(o2):
        if o2 < 90:
            add("O2Sat", float(o2), 0.25, f"Сатурация: {o2:.0f}% (низкая) — повышает риск", "повышает риск")
        elif o2 < 94:
            add("O2Sat", float(o2), 0.12, f"Сатурация: {o2:.0f}% (снижена) — повышает риск", "повышает риск")

    temp = row.get("Temp", np.nan)
    if pd.notna(temp):
        if temp >= 38.5:
            add("Temp", float(temp), 0.18, f"Температура: {temp:.1f} °C (высокая) — повышает риск", "повышает риск")
        elif temp >= 38.0:
            add("Temp", float(temp), 0.10, f"Температура: {temp:.1f} °C (повышена) — повышает риск", "повышает риск")
        elif temp <= 35.5:
            add("Temp", float(temp), 0.15, f"Температура: {temp:.1f} °C (низкая) — повышает риск", "повышает риск")

    sbp = row.get("SBP", np.nan)
    if pd.notna(sbp):
        if sbp < 90:
            add("SBP", float(sbp), 0.22, f"САД: {sbp:.0f} мм рт.ст. (низкое) — повышает риск", "повышает риск")
        elif sbp < 100:
            add("SBP", float(sbp), 0.10, f"САД: {sbp:.0f} мм рт.ст. (снижено) — повышает риск", "повышает риск")

    resp = row.get("Resp", np.nan)
    if pd.notna(resp):
        if resp >= 25:
            add("Resp", float(resp), 0.15, f"ЧД: {resp:.0f}/мин (высокая) — повышает риск", "повышает риск")
        elif resp >= 22:
            add("Resp", float(resp), 0.08, f"ЧД: {resp:.0f}/мин (повышена) — повышает риск", "повышает риск")

    lactate = row.get("Lactate", np.nan)
    if pd.notna(lactate) and lactate >= 2.0:
        add("Lactate", float(lactate), 0.18, f"Лактат: {lactate:.1f} — повышает риск", "повышает риск")

    score = float(np.clip(score, 0.0, 0.95))
    factors.sort(key=lambda f: abs(f["contribution"]), reverse=True)
    return score, factors[:5]


def _predict_stub(patient_df: pd.DataFrame) -> RiskResult:
    df = patient_df.copy()
    if "ICULOS" not in df.columns:
        df["ICULOS"] = np.arange(1, len(df) + 1, dtype=float)

    hours, risks, alerts, factors_all = [], [], [], []
    for _, row in df.iterrows():
        risk, factors = _stub_score_row(row)
        hours.append(float(row["ICULOS"]))
        risks.append(risk)
        alerts.append(risk >= STUB_THRESHOLD)
        factors_all.append(factors)

    return RiskResult(
        hours=hours,
        risks=risks,
        alerts=alerts,
        factors_per_hour=factors_all,
        threshold=STUB_THRESHOLD,
        backend="stub",
        latest_risk=risks[-1] if risks else 0.0,
        latest_alert=alerts[-1] if alerts else False,
        latest_factors=factors_all[-1] if factors_all else [],
    )


def _predict_mqea(patient_df: pd.DataFrame, top_k: int = 5) -> RiskResult:
    load_model, predict = _try_import_mqea()
    assert load_model is not None and predict is not None
    model = load_model()
    # Drop label if present (demo CSVs may include it)
    df = patient_df.drop(columns=["SepsisLabel"], errors="ignore")
    out = predict(df, explain=True, top_k=top_k)
    hours = [float(h) for h in out["hour"].tolist()]
    risks = [float(r) for r in out["risk"].tolist()]
    alerts = [bool(a) for a in out["alert"].tolist()]
    factors = [list(f) if isinstance(f, (list, tuple)) else [] for f in out["factors"].tolist()]
    return RiskResult(
        hours=hours,
        risks=risks,
        alerts=alerts,
        factors_per_hour=factors,
        threshold=float(model.threshold),
        backend="mqea_ew",
        latest_risk=risks[-1] if risks else 0.0,
        latest_alert=alerts[-1] if alerts else False,
        latest_factors=factors[-1] if factors else [],
    )


def predict_risk(patient_df: pd.DataFrame, top_k: int = 5) -> RiskResult:
    """Public API: MQEA-EW when usable, otherwise vitals stub."""
    if patient_df is None or len(patient_df) == 0:
        raise ValueError("patient_df is empty")
    if mqea_available():
        try:
            return _predict_mqea(patient_df, top_k=top_k)
        except Exception:
            # Fall through to stub rather than crashing the demo UI
            pass
    return _predict_stub(patient_df)


def summary_for_llm(result: RiskResult) -> dict[str, Any]:
    """Compact structured payload for the Nemotron prompt."""
    return {
        "backend": result.backend,
        "threshold": result.threshold,
        "latest_risk": round(result.latest_risk, 4),
        "latest_alert": result.latest_alert,
        "max_risk": round(max(result.risks) if result.risks else 0.0, 4),
        "n_hours": len(result.hours),
        "top_factors": [
            {
                "name": f.get("name_ru") or f.get("variable"),
                "effect": f.get("effect"),
                "text": f.get("text"),
                "contribution": round(float(f.get("contribution", 0)), 5),
            }
            for f in result.latest_factors
        ],
    }
