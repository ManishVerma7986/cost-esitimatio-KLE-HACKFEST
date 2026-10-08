"""Page 2: Interactive Work Breakdown Structure (WBS) Editor."""

import sys
from pathlib import Path
import uuid
import pandas as pd
import streamlit as st

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

st.set_page_config(page_title="WBS Editor | Costimator", page_icon="📝", layout="wide")

from streamlit_app.components.api_client import (
    get_db_session,
    get_default_user,
    get_project_by_id,
    list_all_projects,
    run_project_estimate,
)
from streamlit_app.components.styles import apply_custom_css
from app.db.models.work_item import WorkItem
from app.services.wbs import get_project_work_items

apply_custom_css()

st.markdown('<div class="hero-title">📝 Work Breakdown Structure (WBS) Editor</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Refine task allocations, adjust roles and complexities, or enter manual hour overrides with full modification tracking.</div>',
    unsafe_allow_html=True,
)

db = get_db_session()
user = get_default_user(db)
projects = list_all_projects(db)

if not projects:
    st.warning("No projects found. Please create a project first via 'New Estimate'.")
    st.page_link("pages/01_New_Estimate.py", label="Create New Project", icon="➕")
    db.close()
    st.stop()

# Project Selection
project_map = {f"{p.name} ({p.status.upper()})": p.id for p in projects}
selected_name = st.selectbox("Select Project Workspace:", list(project_map.keys()))
project_id = project_map[selected_name]

items = get_project_work_items(db, project_id)

if not items:
    st.info("This project does not have any WBS items yet. Run AI decomposition from the New Estimate page.")
    if st.button("Trigger AI Decomposition Now"):
        from streamlit_app.components.api_client import run_ai_decomposition
        run_ai_decomposition(db, project_id, user.id)
        st.success("Decomposition completed!")
        st.rerun()
    db.close()
    st.stop()

# Build DataFrame for st.data_editor
rows = []
for it in items:
    rows.append({
        "ID": str(it.id),
        "Phase": it.phase,
        "Task Name": it.name,
        "Role": it.role or "Software Engineer",
        "Complexity": it.complexity,
        "Priority": it.priority,
        "Estimated Hours": float(it.estimated_hours) if it.estimated_hours is not None else 0.0,
        "User Modified": it.is_user_modified,
    })

df = pd.DataFrame(rows)

col_ctrl1, col_ctrl2 = st.columns([3, 1])
with col_ctrl1:
    st.caption(f"Displaying {len(df)} work items across {df['Phase'].nunique()} phases. Edit cells directly in the table below.")

edited_df = st.data_editor(
    df,
    disabled=["ID", "User Modified"],
    column_config={
        "Complexity": st.column_config.SelectboxColumn(
            "Complexity", options=["low", "medium", "high", "very_high"], required=True
        ),
        "Priority": st.column_config.SelectboxColumn(
            "Priority", options=["low", "medium", "high", "critical"], required=True
        ),
        "Estimated Hours": st.column_config.NumberColumn(
            "Estimated Hours (Override)", min_value=0.0, max_value=2000.0, step=4.0
        ),
    },
    use_container_width=True,
    num_rows="dynamic",
    key="wbs_table_editor",
)

col_act1, col_act2 = st.columns([1, 1])
with col_act1:
    if st.button("💾 Save WBS Edits to Database", use_container_width=True):
        # Apply updates
        for idx, row in edited_df.iterrows():
            item_id_val = row.get("ID")
            if pd.notna(item_id_val) and str(item_id_val).strip():
                try:
                    it = db.get(WorkItem, uuid.UUID(str(item_id_val).strip()))
                    if it:
                        it.name = str(row["Task Name"])
                        it.phase = str(row["Phase"])
                        it.role = str(row["Role"])
                        it.complexity = str(row["Complexity"])
                        it.priority = str(row["Priority"])
                        hours = float(row["Estimated Hours"]) if pd.notna(row["Estimated Hours"]) else 0.0
                        if hours > 0 and hours != it.estimated_hours:
                            it.estimated_hours = hours
                            it.is_user_modified = True
                except (ValueError, TypeError):
                    pass
            elif pd.notna(row.get("Task Name")) and str(row.get("Task Name")).strip():
                # Dynamic row added directly in data editor
                new_item = WorkItem(
                    id=uuid.uuid4(),
                    project_id=project_id,
                    name=str(row["Task Name"]).strip(),
                    phase=str(row.get("Phase", "Development")),
                    role=str(row.get("Role", "Software Engineer")),
                    complexity=str(row.get("Complexity", "medium")),
                    priority=str(row.get("Priority", "medium")),
                    estimated_hours=float(row["Estimated Hours"]) if pd.notna(row.get("Estimated Hours")) and float(row["Estimated Hours"]) > 0 else 40.0,
                    is_user_modified=True,
                    modification_note="Created in WBS table editor",
                )
                db.add(new_item)
        db.commit()
        st.success("WBS changes saved successfully!")
        st.rerun()

with col_act2:
    if st.button("⚡ Calculate Multi-Model Estimate & Quantify Uncertainty ➡️", type="primary", use_container_width=True):
        with st.spinner("Running COCOMO-II parametric baseline, ML model, and 10,000-run Monte Carlo simulation..."):
            run_project_estimate(db, project_id, user.id)
            st.session_state["selected_project_id"] = str(project_id)
            st.success("Estimate generated!")
            st.switch_page("pages/03_Estimate_Workspace.py")

db.close()
