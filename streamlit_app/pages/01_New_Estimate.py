"""Page 1: Project Scope Input & AI Scope Decomposition."""

import json
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import streamlit as st

st.set_page_config(page_title="New Estimate | Costimator", page_icon="➕", layout="wide")

from streamlit_app.components.api_client import (
    create_new_project,
    get_db_session,
    get_default_user,
    run_ai_decomposition,
)
from streamlit_app.components.styles import apply_custom_css

apply_custom_css()

st.markdown('<div class="hero-title">➕ Create Project & AI Scope Decomposition</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Describe your software system in natural language. Our AI engine decomposes requirements into an actionable Work Breakdown Structure.</div>',
    unsafe_allow_html=True,
)

db = get_db_session()
user = get_default_user(db)

with st.form("new_project_form"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Project Name *", placeholder="e.g. Real-Time Telehealth Consultation App")
        product_type = st.selectbox(
            "Product Type",
            ["SaaS Web Application", "Mobile Application (iOS/Android)", "Cloud API & Backend", "AI/ML Data Platform", "E-Commerce System", "Internal Enterprise Tool"],
        )
        industry = st.selectbox(
            "Industry Domain",
            ["FinTech & Banking", "HealthTech & MedTech", "E-Commerce & Retail", "EdTech", "Logistics & Supply Chain", "General Enterprise SaaS"],
        )

    with col2:
        target_platform = st.text_input("Target Platforms", value="Cloud Native / Web / Mobile")
        expected_users = st.text_input("Expected Scale / Concurrent Users", value="10,000 - 50,000 MAU")
        required_integrations = st.text_input(
            "Required Integrations", placeholder="e.g. Stripe, Twilio, Auth0, AWS S3, SendGrid"
        )

    technology_constraints = st.text_area(
        "Technology Constraints (Optional)",
        placeholder="e.g. Must run on AWS with PostgreSQL, Docker containers, React frontend, and Redis cache.",
        height=70,
    )

    description = st.text_area(
        "Detailed Project Scope Description *",
        placeholder=(
            "Describe the product features, user roles, core workflows, administrative features, "
            "security requirements, data storage, and compliance needs in detail..."
        ),
        height=180,
    )

    submitted = st.form_submit_button("⚡ Run AI Scope Decomposition", type="primary", use_container_width=True)

if submitted:
    if not name.strip() or not description.strip():
        st.error("Please provide both a Project Name and a Scope Description.")
    else:
        with st.spinner("Analyzing architecture, extracting requirements, and generating WBS tasks..."):
            try:
                proj_data = {
                    "name": name,
                    "description": description,
                    "product_type": product_type,
                    "industry": industry,
                    "target_platform": target_platform,
                    "expected_users": expected_users,
                    "technology_constraints": technology_constraints,
                    "required_integrations": required_integrations,
                }
                project = create_new_project(db, proj_data, user.id)
                scope, tasks = run_ai_decomposition(db, project.id, user.id)

                req_count = len(json.loads(scope.requirements_json)) if scope.requirements_json else len(tasks)
                st.success(f"Successfully decomposed '{name}' into {len(tasks)} WBS work items across {req_count} functional requirements!")

                # Store active project in session state
                st.session_state["selected_project_id"] = str(project.id)

                st.markdown("### 📋 Generated Work Phases")
                for phase in set(t.phase for t in tasks):
                    phase_tasks = [t for t in tasks if t.phase == phase]
                    with st.expander(f"📁 {phase} ({len(phase_tasks)} tasks)", expanded=True):
                        for pt in phase_tasks:
                            st.markdown(f"• **{pt.name}** — *Role:* `{pt.role}` | *Complexity:* `{pt.complexity}`")

                st.info("👉 Proceed to **WBS Editor** in the sidebar to review task hours or click below:")
                if st.button("Open WBS Editor & Calculate Estimate ➡️", type="primary"):
                    st.switch_page("pages/02_WBS_Editor.py")

            except Exception as exc:
                st.error(f"Error during decomposition: {exc}")

db.close()
