"""Page 9: Immutable Audit Trail and Governance Log."""

from __future__ import annotations

import sys
from pathlib import Path
import json
from datetime import datetime, timezone
import pandas as pd
import streamlit as st

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

st.set_page_config(page_title="Audit Trail | Costimator", page_icon="🛡️", layout="wide")

from streamlit_app.components.api_client import get_audit_logs, get_db_session
from streamlit_app.components.styles import apply_custom_css

apply_custom_css()

st.markdown('<div class="hero-title">🛡️ Audit Trail & Regulatory Compliance</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Immutable, tamper-evident log capturing all project creations, AI scope decompositions, manual WBS alterations, cost calibrations, and system events.</div>',
    unsafe_allow_html=True,
)

db = get_db_session()

# Filter controls
with st.container():
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        action_filter = st.selectbox(
            "Filter by Action",
            [
                "All",
                "create_project",
                "decompose_project",
                "create_task",
                "update_task",
                "delete_task",
                "generate_estimate",
                "create_scenario",
                "dataset_upload",
                "retrain_model",
            ],
        )
    with col2:
        source_filter = st.selectbox("Filter by Source", ["All", "user", "system", "model", "import"])
    with col3:
        record_limit = st.selectbox("Log Limit", [50, 100, 200, 500], index=1)

logs = get_audit_logs(
    db,
    limit=record_limit,
    action_filter=action_filter if action_filter != "All" else None,
    source_filter=source_filter if source_filter != "All" else None,
)

# Metric KPI summary
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.metric("Total Events Logged", len(logs))
with col_m2:
    user_actions = sum(1 for log in logs if log.source == "user")
    st.metric("User Actions", user_actions)
with col_m3:
    ai_actions = sum(1 for log in logs if log.source in ("model", "system"))
    st.metric("System/AI Actions", ai_actions)
with col_m4:
    last_event_time = logs[0].timestamp.strftime("%H:%M:%S") if logs else "N/A"
    st.metric("Latest Event Time", last_event_time)

st.markdown("<br>", unsafe_allow_html=True)

if not logs:
    st.info("No audit logs matching current filter parameters.")
else:
    table_data = []
    for log in logs:
        time_str = log.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC") if log.timestamp else "N/A"
        table_data.append({
            "Log ID": str(log.id)[:8] + "...",
            "Timestamp": time_str,
            "Action": log.action,
            "Entity Type": log.entity_type,
            "Entity ID": str(log.entity_id)[:12] + "..." if log.entity_id else "N/A",
            "Source": log.source.upper(),
            "IP Address": log.ip_address or "127.0.0.1",
        })

    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True)

    # Detailed Inspector
    st.markdown("### 🔍 Event Inspector")
    log_options = {f"{log.timestamp.strftime('%H:%M:%S')} - {log.action} ({str(log.id)[:8]})": log for log in logs}
    selected_event_key = st.selectbox("Select event to inspect details", list(log_options.keys()))

    if selected_event_key:
        event = log_options[selected_event_key]
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown(f"**Action:** `{event.action}`")
            st.markdown(f"**Entity:** `{event.entity_type}` (`{event.entity_id}`)")
            st.markdown(f"**Source:** `{event.source}`")
            st.markdown(f"**User ID:** `{event.user_id}`")
        with col_d2:
            st.markdown(f"**Timestamp:** `{event.timestamp}`")
            st.markdown(f"**IP:** `{event.ip_address or '127.0.0.1'}`")
            st.markdown(f"**Request ID:** `{event.request_id or 'N/A'}`")

        col_v1, col_v2 = st.columns(2)
        with col_v1:
            st.caption("Previous Value / State")
            if event.previous_value:
                try:
                    prev_obj = json.loads(event.previous_value)
                    st.json(prev_obj)
                except Exception:
                    st.code(event.previous_value)
            else:
                st.info("None (Creation or Immutable event)")

        with col_v2:
            st.caption("New Value / State")
            if event.new_value:
                try:
                    new_obj = json.loads(event.new_value)
                    st.json(new_obj)
                except Exception:
                    st.code(event.new_value)
            else:
                st.info("None")

    # Export capabilities
    st.markdown("---")
    col_exp1, col_exp2 = st.columns([1, 4])
    with col_exp1:
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Export Audit Log (CSV)",
            data=csv_bytes,
            file_name=f"audit_trail_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

db.close()
