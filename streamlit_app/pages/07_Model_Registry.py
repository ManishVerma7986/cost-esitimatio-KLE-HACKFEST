"""Page 7: ML Model Registry and Artifact Governance."""

import sys
from pathlib import Path
import json
import pandas as pd
import streamlit as st

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

st.set_page_config(page_title="Model Registry | Costimator", page_icon="🧬", layout="wide")

from app.config import get_settings
from app.db.models.model_registry import ModelVersion
from streamlit_app.components.api_client import get_db_session
from streamlit_app.components.styles import apply_custom_css

apply_custom_css()

st.markdown('<div class="hero-title">🧬 Machine Learning Model Registry</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Version control, hyperparameters, artifact provenance, and deployment lifecycle tracking for software cost models.</div>',
    unsafe_allow_html=True,
)

db = get_db_session()
settings = get_settings()

versions = db.query(ModelVersion).order_by(ModelVersion.created_at.desc()).all()

col_stat1, col_stat2, col_stat3 = st.columns(3)
model_path = Path(settings.model_dir) / "latest_model.joblib"

with col_stat1:
    st.metric("Active Production Artifact", "latest_model.joblib" if model_path.exists() else "None")
with col_stat2:
    st.metric("Total Registered Versions", len(versions))
with col_stat3:
    st.metric("Default Algorithm", "LightGBM Regressor (Ensemble)")

st.markdown("<br>", unsafe_allow_html=True)

if not versions:
    st.info("No explicit database registry entries yet. Models are auto-saved upon training runs.")
else:
    table_rows = []
    for v in versions:
        metrics_dict = json.loads(v.metrics_json) if v.metrics_json else {}
        table_rows.append({
            "Version": v.version,
            "Model Name": v.name,
            "Status": v.status.upper(),
            "MMRE": f"{metrics_dict.get('mmre', 0):.3f}",
            "PRED(25)": f"{metrics_dict.get('pred25', 0):.1f}%",
            "Artifact Location": v.artifact_path or str(model_path),
            "Registered At": v.created_at.strftime("%Y-%m-%d %H:%M"),
        })

    st.dataframe(pd.DataFrame(table_rows), use_container_width=True)

db.close()
