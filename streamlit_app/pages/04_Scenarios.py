"""Page 4: What-If Scenario Modeling and Comparative Analysis."""

import sys
from pathlib import Path
import pandas as pd
import streamlit as st

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

st.set_page_config(page_title="What-If Scenarios | Costimator", page_icon="🎛️", layout="wide")

from app.schemas.scenario import ScenarioCreate, ScenarioModification
from streamlit_app.components.api_client import (
    create_scenario,
    get_db_session,
    get_default_user,
    get_latest_estimate,
    get_scenario_comparison,
    list_all_projects,
)
from streamlit_app.components.charts import plot_scenario_comparison_bars
from streamlit_app.components.styles import apply_custom_css

apply_custom_css()

st.markdown('<div class="hero-title">🎛️ What-If Scenario Planning & Sensitivity</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Simulate schedule compression, rate variances, scope alterations, and team scale to analyze cost deltas before execution.</div>',
    unsafe_allow_html=True,
)

db = get_db_session()
user = get_default_user(db)
projects = list_all_projects(db)

if not projects:
    st.warning("No projects available. Create a project first.")
    db.close()
    st.stop()

project_map = {p.name: p.id for p in projects}
selected_name = st.selectbox("Select Project Workspace:", list(project_map.keys()))
project_id = project_map[selected_name]

estimate = get_latest_estimate(db, project_id)
if not estimate:
    st.info("Calculate a baseline estimate in 'Estimate Workspace' before creating what-if scenarios.")
    db.close()
    st.stop()

# ── Baseline Reference ─────────────────────────────────────────────
st.markdown("#### 📌 Active Baseline Reference")
bcol1, bcol2, bcol3, bcol4 = st.columns(4)
bcol1.metric("Baseline Total Cost", f"${estimate.cost_breakdown.total:,.0f}")
bcol2.metric("Baseline Effort", f"{estimate.total_effort_hours:,.0f} hrs")
bcol3.metric("Baseline Duration", f"{estimate.estimated_duration_weeks:.1f} wks")
p80_base = float(estimate.uncertainty.p80) if estimate.uncertainty and estimate.uncertainty.p80 else float(estimate.cost_breakdown.total)
bcol4.metric("Baseline P80 Target", f"${p80_base:,.0f}")

st.markdown("---")

# ── Scenario Builder Form ──────────────────────────────────────────
with st.expander("➕ Build New What-If Scenario", expanded=True):
    with st.form("scenario_builder_form"):
        scen_name = st.text_input("Scenario Name *", placeholder="e.g. Fast-Track Accelerated MVP")
        scen_desc = st.text_input("Scenario Hypothesis / Rationale", placeholder="e.g. Add 2 contractors to compress timeline by 3 weeks")

        c1, c2 = st.columns(2)
        with c1:
            team_mult = st.slider("Team Size Multiplier", min_value=0.5, max_value=2.5, value=1.0, step=0.1)
            rate_mult = st.slider("Hourly Rate Multiplier", min_value=0.7, max_value=1.5, value=1.0, step=0.05)

        with c2:
            contingency_pct = st.slider("Contingency Buffer (%)", min_value=5.0, max_value=35.0, value=15.0, step=2.5)
            deadline_target = st.number_input(
                "Target Deadline (Weeks)",
                min_value=2.0,
                max_value=100.0,
                value=float(round(estimate.estimated_duration_weeks, 1)),
                step=1.0,
            )

        add_buffer_hours = st.number_input("Unplanned Scope Buffer (Additional Hours)", min_value=0.0, max_value=1000.0, value=0.0, step=20.0)

        calc_submitted = st.form_submit_button("⚡ Simulate & Compute Scenario", type="primary", use_container_width=True)

    if calc_submitted:
        if not scen_name.strip():
            st.error("Please provide a scenario name.")
        else:
            with st.spinner("Simulating multi-factor variance and Brooks' law overhead..."):
                mods = ScenarioModification(
                    team_size_multiplier=team_mult,
                    rate_multiplier=rate_mult,
                    contingency_percentage=contingency_pct,
                    deadline_weeks=deadline_target if deadline_target != estimate.estimated_duration_weeks else None,
                    additional_work_item_hours=add_buffer_hours if add_buffer_hours > 0 else None,
                )
                scen_req = ScenarioCreate(
                    estimate_id=estimate.id,
                    name=scen_name,
                    description=scen_desc,
                    modifications=mods,
                )
                create_scenario(db=db, scenario_in=scen_req, user_id=user.id)
                st.success(f"Scenario '{scen_name}' calculated and saved!")
                st.rerun()

# ── Comparative Analysis Table & Chart ─────────────────────────────
st.markdown("---")
st.markdown("### 📊 Side-by-Side Scenario Comparison")

comp = get_scenario_comparison(db=db, estimate_id=estimate.id)

if not comp.scenarios:
    st.info("No what-if scenarios computed yet. Use the builder above to model variations.")
else:
    # Prepare comparison table
    comp_rows = [
        {
            "Scenario": "Baseline Estimate",
            "Total Cost ($)": float(comp.baseline_total_cost),
            "Cost Delta ($)": 0.0,
            "Effort (Hours)": float(comp.baseline_effort_hours),
            "Effort Delta (Hrs)": 0.0,
            "Duration (Weeks)": float(comp.baseline_duration_weeks),
            "Duration Delta": 0.0,
            "P80 Reserve ($)": float(comp.baseline_p80 or comp.baseline_total_cost),
        }
    ]

    for s in comp.scenarios:
        comp_rows.append({
            "Scenario": s.name,
            "Total Cost ($)": float(s.total_cost or 0),
            "Cost Delta ($)": float(s.cost_delta or 0),
            "Effort (Hours)": float(s.total_effort_hours or 0),
            "Effort Delta (Hrs)": float(s.effort_delta_hours or 0),
            "Duration (Weeks)": float(s.estimated_duration_weeks or 0),
            "Duration Delta": float(s.duration_delta_weeks or 0),
            "P80 Reserve ($)": float(s.p80 or s.total_cost or 0),
        })

    comp_df = pd.DataFrame(comp_rows)
    st.dataframe(
        comp_df.style.format({
            "Total Cost ($)": "${:,.2f}",
            "Cost Delta ($)": "{:+,.2f}",
            "Effort (Hours)": "{:,.1f}",
            "Effort Delta (Hrs)": "{:+,.1f}",
            "Duration (Weeks)": "{:.1f}",
            "Duration Delta": "{:+.1f} wks",
            "P80 Reserve ($)": "${:,.2f}",
        }),
        use_container_width=True,
    )

    # Plot Comparison Chart
    fig_comp = plot_scenario_comparison_bars([{"name": r["Scenario"], "total_cost": r["Total Cost ($)"], "p80": r["P80 Reserve ($)"]} for r in comp_rows])
    st.plotly_chart(fig_comp, use_container_width=True)

db.close()
