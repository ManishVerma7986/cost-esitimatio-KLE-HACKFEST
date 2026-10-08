"""Costimator - AI-Powered Software Project Cost Estimation Platform.

Executive Dashboard and landing interface.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import streamlit as st

st.set_page_config(
    page_title="Costimator | AI Cost Estimation",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

from streamlit_app.components.api_client import (
    create_new_project,
    get_db_session,
    get_default_user,
    list_all_projects,
    run_ai_decomposition,
    run_project_estimate,
)
from streamlit_app.components.styles import apply_custom_css

apply_custom_css()

# Header
st.markdown('<div class="hero-title">⚡ Costimator Platform</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Production-grade AI scope decomposition, empirical hybrid estimation, and Monte Carlo uncertainty quantification.</div>',
    unsafe_allow_html=True,
)

db = get_db_session()
user = get_default_user(db)
projects = list_all_projects(db)

# Top Metric Cards
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(
        f"""
        <div class="metric-container">
            <div class="metric-title">Total Projects</div>
            <div class="metric-val">{len(projects)}</div>
            <div class="metric-sub">Active Workspaces</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    estimated_count = sum(1 for p in projects if p.status == "estimated")
    st.markdown(
        f"""
        <div class="metric-container">
            <div class="metric-title">Completed Estimates</div>
            <div class="metric-val">{estimated_count}</div>
            <div class="metric-sub">Quantified & Audited</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
        <div class="metric-container">
            <div class="metric-title">ML Model Status</div>
            <div class="metric-val">LightGBM v1.0</div>
            <div class="metric-sub">Trained on NASA93 Benchmark</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        """
        <div class="metric-container">
            <div class="metric-title">Estimation Engine</div>
            <div class="metric-val">Hybrid Ensemble</div>
            <div class="metric-sub">COCOMO-II + Analogy + ML</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# Main Dashboard Content
col_main, col_side = st.columns([2.3, 1])

with col_main:
    st.markdown("### 📁 Project Workspaces")

    if not projects:
        st.info("No projects created yet. Start by creating a project or loading an empirical demo workspace.")

        if st.button("🚀 Load Pre-Configured FinTech Demo Project", type="primary"):
            demo_data = {
                "name": "Global Multi-Currency Payment Gateway",
                "description": (
                    "High-volume cloud payment platform supporting card settlement, multi-tenant merchant portal, "
                    "webhooks, real-time fraud scoring with Redis, PCI-DSS Level 1 compliance, and PostgreSQL audit logging."
                ),
                "product_type": "FinTech SaaS Platform",
                "industry": "Financial Services",
                "target_platform": "AWS Cloud Native",
                "expected_users": "500,000 MAU",
                "technology_constraints": "Python FastAPI, PostgreSQL, Redis, Docker/K8s",
                "required_integrations": "Stripe, Plaid, Datadog, AWS KMS",
            }
            with st.spinner("Initializing project and running AI Scope Decomposition..."):
                proj = create_new_project(db, demo_data, user.id)
                run_ai_decomposition(db, proj.id, user.id)
                run_project_estimate(db, proj.id, user.id)
                st.success("FinTech project initialized, decomposed, and estimated!")
                st.rerun()

    else:
        for p in projects:
            status_badge = {
                "draft": '<span class="badge-amber">Draft</span>',
                "decomposed": '<span class="badge-cyan">Scope Decomposed</span>',
                "estimated": '<span class="badge-emerald">Fully Estimated</span>',
            }.get(p.status, '<span class="badge-cyan">Active</span>')

            st.markdown(
                f"""
                <div class="glass-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="margin: 0; color: #F8FAFC;">{p.name}</h4>
                        {status_badge}
                    </div>
                    <p style="color: #94A3B8; font-size: 0.9rem; margin-top: 8px;">{p.description[:180]}...</p>
                    <div style="display: flex; gap: 16px; font-size: 0.8rem; color: #64748B;">
                        <span>🏷️ <b>Platform:</b> {p.target_platform or 'Cloud / Web'}</span>
                        <span>🏢 <b>Domain:</b> {p.industry or 'Technology'}</span>
                        <span>📅 <b>Created:</b> {p.created_at.strftime('%Y-%m-%d')}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

with col_side:
    st.markdown("### ⚡ Quick Navigation")
    st.page_link("pages/01_New_Estimate.py", label="Create New Estimate", icon="➕")
    st.page_link("pages/02_WBS_Editor.py", label="WBS Task Editor", icon="📝")
    st.page_link("pages/03_Estimate_Workspace.py", label="Estimate Workspace", icon="📊")
    st.page_link("pages/04_Scenarios.py", label="What-If Scenarios", icon="🎛️")
    st.page_link("pages/05_Benchmarks.py", label="Model Benchmarks", icon="📈")
    st.page_link("pages/06_Data_Import.py", label="Import Dataset", icon="📥")
    st.page_link("pages/07_Model_Registry.py", label="Model Registry", icon="🧬")
    st.page_link("pages/08_Settings.py", label="System Settings", icon="⚙️")
    st.page_link("pages/09_Audit_Trail.py", label="Audit Log Trail", icon="🛡️")

    st.markdown("---")
    st.markdown("#### 🔒 Security & Provenance")
    st.caption("• SHA-256 Model Artifact Tracking")
    st.caption("• XSS & Formula Injection Defenses")
    st.caption("• COCOMO-II Published Math Baseline")
    st.caption("• Non-Fabricated Monte Carlo Percentiles")

db.close()
