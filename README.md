# TajMed Agent

**Nebius × NVIDIA Global AI Hackathon** · Track: **Best Apps and Agents** · Deadline: **30 Oct 2026**

Russian + Tajik medical **decision-support** agent (not a diagnostic device).  
Author: **Muhammad** (Dushanbe developer). License: **MIT**.

---

## Concept / Концепция

| EN | RU |
|----|----|
| Ingest patient vitals/labs (CSV or demo). | Принимает витальные/лабораторные данные (CSV или демо). |
| Score early-warning risk via existing **MQEA-EW** model when available at `/workspace/mqea_ew` (no retraining). | Оценка риска через существующую модель **MQEA-EW** (если доступна), без переобучения. |
| Fallback: transparent vitals heuristic with a clear TODO. | Запасной вариант: простая эвристика по витальным + TODO. |
| **NVIDIA Nemotron** via **Nebius Token Factory** (OpenAI-compatible API) explains risk in **Russian** and **Tajik**, in simple non-diagnostic language. | **NVIDIA Nemotron** через **Nebius Token Factory** поясняет риск на **русском** и **таджикском** простым, недиагностическим языком. |

---

## How Nebius / Nemotron is used

1. Risk engine returns `latest_risk`, `alert`, and top contributing factors.
2. `agent.py` builds a **structured prompt** (score + factors only — never invents diagnoses).
3. Chat Completions call goes to Nebius Token Factory:

```python
from openai import OpenAI
client = OpenAI(
    api_key=os.environ["NEBIUS_API_KEY"],
    base_url=os.environ.get("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/"),
)
client.chat.completions.create(
    model=os.environ.get("NEBIUS_MODEL", "nvidia/Nemotron-3_5-Lightning"),
    messages=[...],
)
```

Default model placeholder: `nvidia/Nemotron-3_5-Lightning` (override with any Nemotron id from the [Token Factory catalog](https://tokenfactory.nebius.com/model-catalog.md)).

Without `NEBIUS_API_KEY`, the UI and smoke test use a **deterministic mock** explanation so the demo stays runnable offline.

---

## Setup / Установка

```bash
cd /workspace/tajmed-agent
python -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt
cp .env.example .env   # then set NEBIUS_API_KEY if you have one
streamlit run app.py
```

Smoke test (mock always; live call only if key present):

```bash
python scripts/smoke_test.py
```

Optional: point at another MQEA-EW tree with `MQEA_EW_ROOT=/path/to/mqea_ew`.

---

## Project layout

```
tajmed-agent/
  app.py                 # Streamlit UI (RU): CSV/demo, chart, alert, RU/TJ tabs
  agent.py               # Nemotron prompt + Nebius OpenAI client
  tajmed_agent/
    config.py            # env defaults
    risk.py              # MQEA-EW adapter or vitals stub
  demo_data/patient_demo.csv
  scripts/smoke_test.py
  .env.example
  requirements.txt
  LICENSE                # MIT
  README.md
```

Do **not** commit secrets (`.env` is gitignored).

---

## Medical disclaimer / Медицинский дисклеймер

This software is a **hackathon prototype for decision support only**. It is **not** a medical device, does **not** diagnose or prescribe, and has **not** been clinically validated for patients in Tajikistan. A licensed clinician must make all decisions.

Это **прототип поддержки решений** для хакатона. Это **не** медицинское изделие, **не** ставит диагноз и **не** назначает лечение. Клиническая валидация на пациентах Таджикистана не проводилась. Решение принимает только врач.

---

## Hackathon submission notes

- **Track:** Best Apps and Agents  
- **Stack:** Streamlit + MQEA-EW (LightGBM early-warning) + NVIDIA Nemotron on Nebius Token Factory  
- **Languages:** Russian UI; explainer output Russian + Tajik (Cyrillic)  
- **Differentiator:** Bilingual bedside explanations grounded in model factors; offline-friendly mock path  
- **License:** MIT (see `LICENSE`)

---

## MQEA-EW adapter

If `/workspace/mqea_ew/mqea_ew/artifacts/model.txt` exists, `tajmed_agent.risk` imports `mqea_ew.predict` / `load_model` (same pattern as the MQEA-EW app/tests) and returns hourly `risk`, `alert`, and `factors`. Otherwise a stub scores HR / O2Sat / Temp / SBP / Resp / Lactate with an explicit **TODO** to wire a validated model.
