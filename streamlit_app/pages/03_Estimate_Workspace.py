"""Page 3: Full Estimate Workspace and Analytics."""

import sys
from pathlib import Path
import uuid
import streamlit as st

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

st.set_page_config(page_title="Estimate Workspace | Costimator", page_icon="📊", layout="wide")

from app.db.models.risk import Risk
from app.utils.export import (
    export_estimate_csv,
    export_estimate_excel,
    export_estimate_json,
    export_estimate_pdf,
)
from streamlit_app.components.api_client import (
    get_db_session,
    get_default_user,
    get_latest_estimate,
    get_project_by_id,
    list_all_projects,
    run_project_estimate,
)
from streamlit_app.components.charts import (
    plot_cost_breakdown_donut,
    plot_monte_carlo_distribution,
)
from streamlit_app.components.styles import apply_custom_css

apply_custom_css()

db = get_db_session()
user = get_default_user(db)
projects = list_all_projects(db)

if not projects:
    st.warning("No projects found. Create one from New Estimate first.")
    st.page_link("pages/01_New_Estimate.py", label="Create Project", icon="➕")
    db.close()
    st.stop()

# Project Picker
project_map = {p.name: p.id for p in projects}
default_idx = 0
if "selected_project_id" in st.session_state:
    for idx, (pname, pid) in enumerate(project_map.items()):
        if str(pid) == st.session_state["selected_project_id"]:
            default_idx = idx
            break

col_head1, col_head2 = st.columns([2.5, 1])
with col_head1:
    selected_name = st.selectbox("Active Project:", list(project_map.keys()), index=default_idx)
    project_id = project_map[selected_name]
    project = get_project_by_id(db, project_id)

with col_head2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Recalculate Estimate", use_container_width=True):
        with st.spinner("Recalculating..."):
            run_project_estimate(db, project_id, user.id)
            st.rerun()

estimate = get_latest_estimate(db, project_id)

if not estimate:
    st.info("This project has not been estimated yet. Click below to run the hybrid estimation engine:")
    if st.button("⚡ Run Full Estimate Calculation Now", type="primary"):
        with st.spinner("Calculating estimate..."):
            run_project_estimate(db, project_id, user.id)
            st.rerun()
    db.close()
    st.stop()

cb = estimate.cost_breakdown
unc = estimate.uncertainty

# ── Top KPI Cards ──────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.markdown(
        f"""
        <div class="metric-container">
            <div class="metric-title">Total Estimated Cost</div>
            <div class="metric-val">${cb.total:,.0f}</div>
            <div class="metric-sub">Base Subtotal + Buffer</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi2:
    st.markdown(
        f"""
        <div class="metric-container">
            <div class="metric-title">Engineering Effort</div>
            <div class="metric-val">{estimate.total_effort_hours:,.0f} hrs</div>
            <div class="metric-sub">{(estimate.total_effort_hours / 152.0):.1f} Person-Months</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi3:
    st.markdown(
        f"""
        <div class="metric-container">
            <div class="metric-title">Duration / Schedule</div>
            <div class="metric-val">{estimate.estimated_duration_weeks:.1f} wks</div>
            <div class="metric-sub">{(estimate.estimated_duration_weeks / 4.33):.1f} Calendar Months</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi4:
    p50_val = float(unc.p50) if unc and unc.p50 else float(cb.total)
    st.markdown(
        f"""
        <div class="metric-container">
            <div class="metric-title">P50 Expected (Median)</div>
            <div class="metric-val" style="color: #34D399;">${p50_val:,.0f}</div>
            <div class="metric-sub">50% Likelihood Milestone</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi5:
    p80_val = float(unc.p80) if unc and unc.p80 else float(cb.total)
    st.markdown(
        f"""
        <div class="metric-container">
            <div class="metric-title">P80 Budget Target</div>
            <div class="metric-val" style="color: #FBBF24;">${p80_val:,.0f}</div>
            <div class="metric-sub">Executive 80% Reserve</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Visual Analytics: Donut & Distribution Curve ───────────────────
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("#### 🍩 Cost Category Breakdown")
    fig_donut = plot_cost_breakdown_donut(cb.model_dump())
    st.plotly_chart(fig_donut, use_container_width=True)

with chart_col2:
    st.markdown("#### 📈 Monte Carlo Uncertainty Distribution (10k Runs)")
    if unc:
        p10_f = float(unc.p10 or cb.total * 0.85)
        p50_f = float(unc.p50 or cb.total)
        p80_f = float(unc.p80 or cb.total * 1.15)
        p90_f = float(unc.p90 or cb.total * 1.25)
        fig_dist = plot_monte_carlo_distribution(p10_f, p50_f, p80_f, p90_f, float(cb.total))
        st.plotly_chart(fig_dist, use_container_width=True)

# ── Executive Advisory & Cost Drivers ──────────────────────────────
st.markdown("---")
adv_col1, adv_col2 = st.columns([1.4, 1])

with adv_col1:
    st.markdown("#### 💡 Executive Advisory & Recommendation")
    if estimate.recommendation:
        st.markdown(
            f"""
            <div class="glass-card" style="border-left: 4px solid #38BDF8;">
                <p style="font-size: 0.95rem; line-height: 1.6; color: #E2E8F0;">
                    {estimate.recommendation}
                </p>
                <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 12px;">
                    <b>Model Provenance:</b> {estimate.estimation_method} | <b>Cycle Time:</b> {estimate.estimation_cycle_time_seconds or 0.1:.2f}s
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with adv_col2:
    st.markdown("#### 🔍 Primary Cost Drivers")
    for driver in estimate.cost_drivers:
        st.markdown(
            f"""
            <div style="margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 3px;">
                    <span style="color: #F8FAFC; font-weight: 600;">{driver.feature_name}</span>
                    <span style="color: #38BDF8; font-weight: 700;">{driver.contribution_pct}%</span>
                </div>
                <div style="background: rgba(255,255,255,0.08); border-radius: 4px; height: 6px; overflow: hidden;">
                    <div style="background: #38BDF8; width: {driver.contribution_pct}%; height: 100%;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Detected Project Risks ─────────────────────────────────────────
st.markdown("---")
st.markdown("#### 🛡️ Grounded Project Risks & Mitigations")
risks = db.query(Risk).filter(Risk.estimate_id == estimate.id).all()

if risks:
    r_cols = st.columns(len(risks) if len(risks) <= 3 else 3)
    for idx, r in enumerate(risks):
        col_target = r_cols[idx % len(r_cols)]
        badge_cls = "badge-rose" if r.severity in ("high", "critical") else "badge-amber"
        with col_target:
            st.markdown(
                f"""
                <div class="glass-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 0.75rem; color: #94A3B8; font-weight: 600;">{r.category}</span>
                        <span class="{badge_cls}">{r.severity.upper()}</span>
                    </div>
                    <b style="color: #F8FAFC; font-size: 0.95rem;">{r.title}</b>
                    <p style="font-size: 0.82rem; color: #CBD5E1; margin: 8px 0;"><b>Evidence:</b> {r.evidence}</p>
                    <p style="font-size: 0.82rem; color: #34D399; margin: 0;"><b>Mitigation:</b> {r.mitigation}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
else:
    st.success("No critical variance risks flagged for current scope parameters.")

# ── Itemized Line Items ────────────────────────────────────────────
st.markdown("---")
with st.expander("📄 View Complete Itemized Line Items Table", expanded=False):
    import pandas as pd
    item_rows = [
        {
            "Category": c.category.title(),
            "Subcategory": c.subcategory or "",
            "Description": c.name,
            "Quantity": f"{c.quantity:,.1f}" if c.quantity else "",
            "Unit": c.unit or "",
            "Unit Cost": f"${c.unit_cost:.2f}" if c.unit_cost else "",
            "Total Amount": f"${c.total_amount:,.2f}",
            "Formula / Notes": c.formula or "",
        }
        for c in estimate.components
    ]
    st.dataframe(pd.DataFrame(item_rows), use_container_width=True)

# ── Export Action Center ───────────────────────────────────────────
st.markdown("---")
st.markdown("#### 📥 Export Audit-Ready Reports")
exp1, exp2, exp3, exp4 = st.columns(4)

proj_name = project.name if project else "Project"

with exp1:
    csv_bytes = export_estimate_csv(estimate, proj_name)
    st.download_button(
        "📄 Download CSV",
        data=csv_bytes,
        file_name=f"{project_id}_estimate.csv",
        mime="text/csv",
        use_container_width=True,
    )

with exp2:
    json_bytes = export_estimate_json(estimate, proj_name)
    st.download_button(
        "🗂️ Download JSON",
        data=json_bytes,
        file_name=f"{project_id}_estimate.json",
        mime="application/json",
        use_container_width=True,
    )

with exp3:
    excel_bytes = export_estimate_excel(estimate, proj_name)
    st.download_button(
        "📊 Download Excel (.xlsx)",
        data=excel_bytes,
        file_name=f"{project_id}_estimate.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

with exp4:
    pdf_bytes = export_estimate_pdf(estimate, proj_name)
    st.download_button(
        "📕 Download PDF Brief",
        data=pdf_bytes,
        file_name=f"{project_id}_executive_brief.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )

db.close()
