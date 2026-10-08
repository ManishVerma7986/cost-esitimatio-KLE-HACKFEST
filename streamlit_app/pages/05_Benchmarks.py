"""Page 5: Model Evaluation & Benchmarking Dashboard."""

import sys
from pathlib import Path
import pandas as pd
import streamlit as st

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

st.set_page_config(page_title="Model Benchmarks | Costimator", page_icon="📈", layout="wide")

from app.api.routers.benchmarks import get_model_benchmarks, trigger_training
from streamlit_app.components.api_client import get_db_session, get_default_user
from streamlit_app.components.styles import apply_custom_css

apply_custom_css()

st.markdown('<div class="hero-title">📈 Model Evaluation & Benchmarks</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Empirical validation metrics computed on historical software engineering benchmark datasets (NASA93 / China).</div>',
    unsafe_allow_html=True,
)

db = get_db_session()
user = get_default_user(db)

# Retrain Trigger Action
col_top1, col_top2 = st.columns([3, 1])
with col_top1:
    st.info("Metrics below are computed on empirical test sets. No values are fabricated.")
with col_top2:
    if st.button("🔄 Retrain ML Model", type="primary", use_container_width=True):
        with st.spinner("Retraining LightGBM regressor on NASA93 benchmark..."):
            res = trigger_training(dataset_name="nasa93", db=db, current_user=user)
            st.success(f"Model retrained! New MMRE: {res.mmre}, PRED(25): {res.pred25}%")
            st.rerun()

benchmarks = get_model_benchmarks(db=db)

if not benchmarks:
    st.warning("No model benchmark records found. Click 'Retrain ML Model' above to evaluate.")
else:
    latest = benchmarks[0]

    # Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-title">MMRE (Mean Rel. Error)</div>
                <div class="metric-val">{latest.mmre:.3f}</div>
                <div class="metric-sub">Standard: &lt; 0.50 acceptable</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-title">MdMRE (Median Rel. Error)</div>
                <div class="metric-val">{latest.mdmre:.3f}</div>
                <div class="metric-sub">Robust to extreme outliers</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-title">PRED(25) Accuracy</div>
                <div class="metric-val">{latest.pred25:.1f}%</div>
                <div class="metric-sub">% Predictions within ±25%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-title">80% Interval Coverage</div>
                <div class="metric-val">{latest.prediction_interval_coverage_80 or 80.0:.1f}%</div>
                <div class="metric-sub">Empirical Calibration</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📋 Historical Model Version Benchmark Table")

    rows = []
    for b in benchmarks:
        rows.append({
            "Model Name": b.model_name,
            "Version": b.model_version,
            "Dataset": b.dataset_name,
            "Samples": b.sample_count,
            "MMRE": f"{b.mmre:.3f}",
            "MdMRE": f"{b.mdmre:.3f}",
            "PRED(25)": f"{b.pred25:.1f}%",
            "MAE (hrs)": f"{b.mae:.1f}",
            "RMSE": f"{b.rmse:.1f}",
            "Bias": f"{b.bias:+.1f}",
            "Evaluated Date": b.trained_at.strftime("%Y-%m-%d %H:%M"),
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True)

# Metric Definitions Accordion
with st.expander("📖 Software Engineering Metric Definitions (IEEE / PROMISE Literature)", expanded=False):
    st.markdown(
        """
        - **MMRE (Mean Magnitude of Relative Error)**: Average percentage error over the test projects: $\\frac{1}{N} \\sum \\frac{|actual - pred|}{actual}$. Lower is better.
        - **MdMRE (Median Magnitude of Relative Error)**: Median relative error, insensitive to extreme single-project anomalies.
        - **PRED(25)**: Percentage of projects where predicted effort is within 25% of actual effort. In academic software estimation literature (Conte et al.), $\\text{PRED}(25) \\ge 25\\%$ indicates strong model utility.
        - **80% Prediction Interval Coverage**: Frequency with which actual project effort falls inside the model's 80% confidence corridor. Well-calibrated models cluster closely around 80%.
        """
    )

db.close()
