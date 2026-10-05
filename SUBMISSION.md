# Hackathon submission checklist / Чеклист подачи

**Event:** [Nebius × NVIDIA Global AI Hackathon](https://nebiusglobalaihackathon.devpost.com/)  
**Deadline:** 30 Oct 2026 @ 10:00am PDT  
**Track:** **Best Apps and Agents**  
**Repo:** https://github.com/Fopen1/tajmed-agent  
**Must use:** Nebius Token Factory **or** Nebius AI Cloud **+** at least one NVIDIA open model (Nemotron / GR00T / Cosmos / Sonic)

---

## EN — What to submit

| # | Requirement | Status / notes |
|---|-------------|----------------|
| 1 | **Working project** on Token Factory or AI Cloud using NVIDIA open models | TajMed Agent: Nemotron via Token Factory Chat Completions |
| 2 | **Track selected:** Best Apps and Agents | Primary track |
| 3 | **Project description** on Devpost (what / why / how) | Fill on Devpost form |
| 4 | **Demo URL** or clear how-to-run | Local: `streamlit run app.py` (see README). Hosted URL: _TODO when deployed_ |
| 5 | **Demo video ≤ 3 min** (public YouTube) showing Nebius + Nemotron in use | _TODO record_ |
| 6 | **Public code repo** (GitHub) with **open-source license** visible at top | MIT (`LICENSE`); repo must stay public |
| 7 | **README** with setup + how NVIDIA Nemotron / Token Factory are used | This repo |
| 8 | Feedback on Nebius / NVIDIA tools (Devpost field) | Optional but prize-eligible (“Most Valuable Feedback”) |
| 9 | If pre-existing code: explain what changed in submission period | Note MQEA-EW is separate sibling risk model; agent built for hackathon |

### How to run (judges)

```bash
git clone https://github.com/Fopen1/tajmed-agent.git
cd tajmed-agent
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # set NEBIUS_API_KEY from https://tokenfactory.nebius.com/
streamlit run app.py
```

Without a key, the UI still runs with an offline mock explanation (risk scoring works via MQEA-EW or vitals stub).

### Credits setup (before live demo)

1. Sign up at [tokenfactory.nebius.com](https://tokenfactory.nebius.com/)
2. Apply promo **`NEBIUS-DEVPOST-GLOBAL26`**: balance → Top up → With promo code → apply ([resources](https://nebiusglobalaihackathon.devpost.com/resources))
3. Optional: Nebius Builders Program for another ~$25
4. API keys → Create API key → save once → put in `.env` as `NEBIUS_API_KEY`
5. Default model: `nvidia/Nemotron-3_5-Lightning` (`NEBIUS_BASE_URL=https://api.tokenfactory.nebius.com/v1/`)

### Official rules reminder

Full rules: Devpost → Official Rules. All submissions must run on Token Factory or AI Cloud and use ≥1 NVIDIA open model. Video must show the project working and how Nebius + Nemotron were used.

---

## RU — Краткий чеклист

| # | Требование | Заметка |
|---|------------|---------|
| 1 | Рабочий проект на **Nebius Token Factory** или **AI Cloud** + NVIDIA open model | Nemotron через Token Factory |
| 2 | Трек **Best Apps and Agents** | Основной трек |
| 3 | Описание на Devpost | Что / зачем / как |
| 4 | **Demo URL** или инструкция запуска | `streamlit run app.py` / URL хостинга — TODO |
| 5 | Видео **≤ 3 мин** (YouTube) | Показать Nebius + Nemotron |
| 6 | **Публичный** репозиторий + лицензия (MIT) | https://github.com/Fopen1/tajmed-agent |
| 7 | README с установкой и объяснением стека | Есть |
| 8 | Промокод **`NEBIUS-DEVPOST-GLOBAL26`** на кредиты | Top up → With promo code |

### Запуск

```bash
pip install -r requirements.txt
cp .env.example .env   # вставить NEBIUS_API_KEY
streamlit run app.py
```

Без ключа работает mock-пояснение; риск считается через MQEA-EW (если рядом) или заглушку по витальным.

---

## Pre-submit checklist (tick before Devpost submit)

- [ ] Repo is **public**; `LICENSE` (MIT) visible
- [ ] README + this `SUBMISSION.md` up to date
- [ ] Live Nemotron call works with real `NEBIUS_API_KEY`
- [ ] Demo URL **or** judges can run from README in &lt;5 min
- [ ] YouTube video ≤ 3:00 uploaded and linked
- [ ] Devpost track = **Best Apps and Agents**
- [ ] Screenshots / GIF in README or Devpost gallery (optional but recommended)
- [ ] No secrets in git (`.env` gitignored)
