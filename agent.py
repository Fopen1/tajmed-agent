"""Nemotron explanation agent via Nebius Token Factory (OpenAI-compatible API).

Takes risk score + top factors → plain-language explanations in Russian and Tajik.
Never invents diagnoses; language stays non-diagnostic / decision-support only.

Graceful degradation:
- No NEBIUS_API_KEY → deterministic mock (offline demo / smoke_test).
- Auth / bad model / network / API errors → mock + structured error fields
  (UI stays usable; smoke_test with mock=True always works).
"""
from __future__ import annotations

from typing import Any

from tajmed_agent.config import nebius_api_key, nebius_base_url, nebius_model
from tajmed_agent.risk import RiskResult, summary_for_llm

SYSTEM_PROMPT = """You are TajMed Agent — a bilingual (Russian + Tajik) clinical decision-support
assistant for early-warning scores based on patient vitals and labs.

Strict rules:
1. You are NOT a doctor and MUST NOT diagnose, prescribe, or invent disease names.
2. Explain the risk score and the listed factors in simple, calm, non-diagnostic language.
3. Say clearly that this is decision support only; a clinician must decide.
4. Use ONLY the factors and numbers provided. Do not invent labs, symptoms, or history.
5. If data are incomplete, say so briefly.
6. Keep each language block short (4–8 sentences).
7. Output exactly two sections with these headers:
   ### RU
   ### TJ
"""


def build_user_prompt(summary: dict[str, Any], language_hint: str = "ru+tj") -> str:
    factors = summary.get("top_factors") or []
    lines = [
        "Explain this early-warning result for a bedside nurse / physician in plain language.",
        f"Backend: {summary.get('backend')}",
        f"Hours observed: {summary.get('n_hours')}",
        f"Latest risk (0–1): {summary.get('latest_risk')}",
        f"Alert at threshold {summary.get('threshold')}: {summary.get('latest_alert')}",
        f"Max risk in window: {summary.get('max_risk')}",
        "Top contributing factors (from the model, do not invent others):",
    ]
    if not factors:
        lines.append("- (no factor list available)")
    else:
        for i, f in enumerate(factors, 1):
            lines.append(
                f"{i}. {f.get('name')}: {f.get('text')} "
                f"(effect={f.get('effect')}, contribution={f.get('contribution')})"
            )
    lines.append(
        "Remind the reader this is not a diagnosis and was not clinically validated "
        "for Tajikistan patients."
    )
    lines.append(f"Language sections required: {language_hint}")
    return "\n".join(lines)


def _mock_explanation(summary: dict[str, Any]) -> dict[str, str]:
    """Deterministic offline explanation when no API key is set."""
    risk = summary.get("latest_risk", 0)
    alert = summary.get("latest_alert", False)
    factors = summary.get("top_factors") or []
    factor_ru = "; ".join(f.get("text") or str(f.get("name")) for f in factors[:3]) or "факторы не указаны"
    level_ru = "повышенный" if alert else "низкий/умеренный"
    level_tj = "баланд" if alert else "паст/миёна"
    ru = (
        f"Текущий показатель раннего предупреждения: {risk:.1%} ({level_ru} относительно порога "
        f"{summary.get('threshold')}). Основные вкладные признаки: {factor_ru}. "
        "Это система поддержки решений, а не диагноз. Интерпретацию и дальнейшие действия "
        "определяет только врач. Модель не проходила клиническую валидацию на пациентах Таджикистана."
    )
    tj = (
        f"Нишондиҳандаи огоҳии барвақт: {risk:.1%} (сатҳи {level_tj} нисбат ба ҳадди "
        f"{summary.get('threshold')}). Омилҳои асосӣ аз рӯи модел дода шудаанд; бештар аз онҳо "
        "ташхис наменамоем. Ин танҳо дастгирии қабули қарор аст, на ташхис. Қарори ниҳоӣ "
        "танҳо аз табиб аст. Модел дар беморони Тоҷикистон санҷида нашудааст."
    )
    return {"ru": ru, "tj": tj, "raw": f"### RU\n{ru}\n\n### TJ\n{tj}", "mocked": True}


def _parse_sections(text: str) -> dict[str, str]:
    ru, tj = "", ""
    current = None
    for line in (text or "").splitlines():
        s = line.strip()
        if s.upper().startswith("### RU"):
            current = "ru"
            continue
        if s.upper().startswith("### TJ"):
            current = "tj"
            continue
        if current == "ru":
            ru += line + "\n"
        elif current == "tj":
            tj += line + "\n"
    return {"ru": ru.strip(), "tj": tj.strip()}


def _classify_api_error(exc: BaseException) -> str:
    """Map OpenAI / HTTP errors to a short, safe user-facing reason (no secrets)."""
    name = type(exc).__name__
    msg = str(exc).lower()
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    if status is None:
        body = getattr(exc, "response", None)
        status = getattr(body, "status_code", None) if body is not None else None

    if status in (401, 403) or "invalid api key" in msg or "authentication" in msg or "unauthorized" in msg:
        return "auth_failed"
    if status == 404 or "model" in msg and ("not found" in msg or "does not exist" in msg or "unknown" in msg):
        return "bad_model"
    if status == 429 or "rate limit" in msg or "quota" in msg:
        return "rate_limited"
    if status is not None and int(status) >= 500:
        return "server_error"
    if name in {"APIConnectionError", "APITimeoutError", "ConnectTimeout", "ReadTimeout", "TimeoutError"}:
        return "network_error"
    if "connection" in msg or "timeout" in msg or "timed out" in msg:
        return "network_error"
    return "api_error"


def explain_risk(
    result: RiskResult,
    *,
    mock: bool | None = None,
    temperature: float = 0.3,
    max_tokens: int = 800,
) -> dict[str, Any]:
    """Call Nemotron (or mock) and return {ru, tj, raw, mocked, model?, error?, error_detail?}.

    Offline-safe: missing key or any live-API failure returns a mock explanation
    plus optional error metadata so the UI can show a caption without crashing.
    """
    summary = summary_for_llm(result)
    key = nebius_api_key()
    use_mock = mock if mock is not None else (key is None)

    if use_mock:
        out = _mock_explanation(summary)
        out["summary"] = summary
        if mock is None and key is None:
            out["error"] = "missing_api_key"
            out["error_detail"] = (
                "NEBIUS_API_KEY is not set. Using offline mock explanation. "
                "Copy .env.example → .env and add a Token Factory key."
            )
        return out

    model = nebius_model()
    try:
        from openai import OpenAI

        client = OpenAI(api_key=key, base_url=nebius_base_url())
        resp = client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(summary)},
            ],
        )
        raw = (resp.choices[0].message.content or "").strip()
        sections = _parse_sections(raw)
        if not sections["ru"] and not sections["tj"]:
            # Model ignored headers — keep full text in RU tab as fallback
            sections = {"ru": raw, "tj": ""}
        return {
            "ru": sections["ru"],
            "tj": sections["tj"],
            "raw": raw,
            "mocked": False,
            "model": model,
            "summary": summary,
        }
    except Exception as exc:  # noqa: BLE001 — demo must never crash on API issues
        reason = _classify_api_error(exc)
        out = _mock_explanation(summary)
        out["summary"] = summary
        out["error"] = reason
        out["error_detail"] = (
            f"Nebius Token Factory call failed ({reason}) for model={model!r}. "
            f"{type(exc).__name__}: {exc}"
        )[:500]
        out["model"] = model
        return out
