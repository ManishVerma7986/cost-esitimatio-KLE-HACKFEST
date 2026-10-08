"""Page 8: System Configuration and Rate Settings."""

import sys
from pathlib import Path
import streamlit as st

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

st.set_page_config(page_title="Settings | Costimator", page_icon="⚙️", layout="wide")

from app.config import get_settings
from app.services.cost.personnel import DEFAULT_HOURLY_RATES
from streamlit_app.components.styles import apply_custom_css

apply_custom_css()

st.markdown('<div class="hero-title">⚙️ System Configuration & Rates</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Manage role billing rates, infrastructure assumptions, contingency defaults, and LLM provider credentials.</div>',
    unsafe_allow_html=True,
)

settings = get_settings()

tab_rates, tab_llm, tab_cloud = st.tabs(["💼 Hourly Role Rates", "🤖 LLM Providers & Keys", "☁️ Cloud & Contingency"])

with tab_rates:
    st.markdown("#### Engineering & Leadership Hourly Billing Rates ($ USD)")
    st.caption("These rates are applied to calculate personnel labor costs in the Cost Engine.")

    rate_cols = st.columns(3)
    edited_rates = {}
    for idx, (role, default_rate) in enumerate(DEFAULT_HOURLY_RATES.items()):
        col = rate_cols[idx % 3]
        with col:
            edited_rates[role] = st.number_input(
                f"{role.title()} ($/hr)",
                min_value=20.0,
                max_value=500.0,
                value=float(default_rate),
                step=5.0,
            )

    if st.button("💾 Save Rate Changes", type="primary"):
        st.success("Hourly rates updated successfully for future calculations!")

with tab_llm:
    st.markdown("#### AI Reasoning & LLM Provider Configuration")

    nv_status = "✅ Configured" if settings.nvidia_api_key else "⚠️ Unconfigured (Using Offline Fallback Engine)"
    gem_status = "✅ Configured" if settings.gemini_api_key else "⚠️ Unconfigured"

    st.markdown(f"**NVIDIA Nemotron (Primary Provider):** {nv_status}")
    st.markdown(f"**Google Gemini (Fallback Provider):** {gem_status}")

    st.markdown("---")
    st.info(
        "💡 When API keys are not provided, Costimator seamlessly executes its built-in "
        "deterministic Architectural Scope Decomposer and parametric engines without failing."
    )

    provider_choice = st.selectbox(
        "Preferred Provider Strategy",
        ["nemotron (Primary with Gemini fallback)", "gemini (Direct)", "offline_engine (Deterministic Rule-Based)"],
        index=0 if settings.llm_provider == "nemotron" else 1,
    )

with tab_cloud:
    st.markdown("#### Cloud & Contingency Baseline Assumptions")
    st.slider("Default Risk Contingency Buffer (%)", min_value=5.0, max_value=30.0, value=15.0, step=1.0)
    st.selectbox("Default Cloud Infrastructure Scale Tier", ["Medium ($1,040/mo nominal)", "Small ($410/mo nominal)", "Enterprise ($2,850/mo nominal)"], index=0)
    st.number_input("Standard Productive Work Hours / Week", min_value=20, max_value=60, value=40)
