"""TajMed Agent — Streamlit UI (Russian) for Nebius x NVIDIA Global AI Hackathon.

Run:  pip install -r requirements.txt && streamlit run app.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from agent import explain_risk
from tajmed_agent.risk import mqea_available, predict_risk

ROOT = Path(__file__).resolve().parent
DEMO = ROOT / "demo_data" / "patient_demo.csv"

st.set_page_config(
    page_title="TajMed Agent · поддержка решений",
    page_icon="🩺",
    layout="wide",
)

DISCLAIMER = (
    "⚠️ **Система поддержки принятия решений, не диагноз.** "
    "Не заменяет осмотр врача, не назначает лечение и не прошла клиническую валидацию "
    "на пациентах Таджикистана. Решения принимает только квалифицированный клиницист. "
    "Объяснения формирует LLM (NVIDIA Nemotron через Nebius Token Factory) на основе "
    "оценки риска и факторов модели — модель может ошибаться."
)

st.title("🩺 TajMed Agent")
st.caption(
    "Русско-таджикский агент поддержки решений · трек Best Apps and Agents · "
    "Nebius × NVIDIA Global AI Hackathon (дедлайн 30 октября 2026)"
)
st.info(DISCLAIMER)

backend_ok = mqea_available()
st.sidebar.header("О системе")
st.sidebar.write(
    "**Риск:** " + ("MQEA-EW (раннее предупреждение)" if backend_ok else "заглушка по витальным (TODO: MQEA-EW)")
)
st.sidebar.write("**Пояснения:** NVIDIA Nemotron via Nebius Token Factory")
st.sidebar.markdown(
    "Переменные окружения: `NEBIUS_API_KEY`, `NEBIUS_BASE_URL`, `NEBIUS_MODEL` "
    "(см. `.env.example`)."
)

source = st.radio(
    "Источник данных",
    ["Демо-пациент", "Загрузить CSV"],
    horizontal=True,
)

df: pd.DataFrame | None = None
if source == "Демо-пациент":
    if DEMO.exists():
        df = pd.read_csv(DEMO)
        st.success(f"Загружен демо-файл: `{DEMO.name}` ({len(df)} строк)")
    else:
        st.error("Файл demo_data/patient_demo.csv не найден.")
else:
    up = st.file_uploader("CSV с витальными / лабораторными (формат PhysioNet 2019 или упрощённый)", type=["csv"])
    if up is not None:
        df = pd.read_csv(up)
        st.success(f"Загружено строк: {len(df)}")

if df is not None:
    with st.expander("Предпросмотр данных", expanded=False):
        st.dataframe(df.head(20), use_container_width=True)

    with st.spinner("Расчёт риска…"):
        result = predict_risk(df)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Риск (последний час)", f"{result.latest_risk:.1%}")
    c2.metric("Макс. риск", f"{max(result.risks):.1%}" if result.risks else "—")
    c3.metric("Порог тревоги", f"{result.threshold:.1%}")
    c4.metric("Бэкенд", result.backend)

    if result.latest_alert:
        st.error("🚨 ТРЕВОГА: риск на последнем часу выше порога. Требуется внимание клинициста.")
    else:
        st.success("✅ Тревоги нет: риск на последнем часу ниже порога (это не исключает патологию).")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=result.hours,
            y=result.risks,
            mode="lines+markers",
            name="Риск",
            line=dict(color="#c62828", width=2),
        )
    )
    fig.add_hline(
        y=result.threshold,
        line_dash="dash",
        line_color="#e65100",
        annotation_text=f"порог {result.threshold:.2f}",
    )
    fig.update_layout(
        title="Динамика риска по часам",
        xaxis_title="Час наблюдения (ICULOS)",
        yaxis_title="Риск (0–1)",
        yaxis=dict(range=[0, 1]),
        height=380,
        margin=dict(l=40, r=20, t=50, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Главные факторы (последний час)")
    if result.latest_factors:
        for f in result.latest_factors:
            effect = f.get("effect", "")
            icon = "🔴" if effect == "повышает риск" else "🟢"
            st.markdown(f"{icon} {f.get('text', f)}")
    else:
        st.write("Факторы недоступны.")

    st.subheader("Пояснение Nemotron (RU / TJ)")
    force_mock = st.checkbox("Только mock-пояснение (без API)", value=False)
    if st.button("Сформировать пояснение", type="primary"):
        with st.spinner("Запрос к Nemotron / mock…"):
            expl = explain_risk(result, mock=True if force_mock else None)
        tab_ru, tab_tj = st.tabs(["Русский", "Тоҷикӣ"])
        with tab_ru:
            st.write(expl.get("ru") or "—")
        with tab_tj:
            st.write(expl.get("tj") or "—")
        if expl.get("mocked"):
            err = expl.get("error")
            if err == "missing_api_key":
                st.caption("Показан offline mock: нет NEBIUS_API_KEY (см. `.env.example`).")
            elif err:
                st.warning(
                    f"API Nebius недоступен (`{err}`). Показан offline mock. "
                    f"Проверьте ключ и `NEBIUS_MODEL`. Детали: {expl.get('error_detail', '')[:240]}"
                )
            else:
                st.caption("Показан offline mock (режим mock или нет ключа).")
        else:
            st.caption(f"Модель: `{expl.get('model')}`")

st.markdown("---")
st.caption(
    "MIT License · TajMed Agent for Nebius × NVIDIA Global AI Hackathon · "
    "Автор: Muhammad (Dushanbe). Не для клинического применения без валидации."
)
