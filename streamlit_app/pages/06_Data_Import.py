"""Page 6: Dataset Import & Automated Data Quality Audit."""

import sys
from pathlib import Path
import io
import json
import uuid
import pandas as pd
import streamlit as st

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

st.set_page_config(page_title="Data Import | Costimator", page_icon="📥", layout="wide")

from app.config import get_settings
from app.db.models.dataset import Dataset, DatasetVersion
from app.ml.data_quality import assess_data_quality
from app.security.file_validator import validate_uploaded_file
from streamlit_app.components.api_client import get_db_session, get_default_user
from streamlit_app.components.styles import apply_custom_css

apply_custom_css()

st.markdown('<div class="hero-title">📥 Dataset Import & Data Quality Engine</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Import software project history (CSV). Automatically checks for missingness, duplicates, outliers (IQR), and constant variance.</div>',
    unsafe_allow_html=True,
)

db = get_db_session()
user = get_default_user(db)
settings = get_settings()

uploaded_file = st.file_uploader(
    "Choose a historical project dataset (.csv, .json)",
    type=["csv", "json"],
    help="Must contain columns for software size (sloc/ksloc) and effort (hours or person-months).",
)

if uploaded_file is not None:
    content = uploaded_file.getvalue()
    try:
        safe_name, ext = validate_uploaded_file(uploaded_file.name, content)
        df = pd.read_csv(io.BytesIO(content)) if ext == ".csv" else pd.read_json(io.BytesIO(content))

        st.success(f"File '{safe_name}' passed pre-flight security scan ({len(content) / 1024:.1f} KB).")

        # Run Data Quality Engine
        report = assess_data_quality(df)

        st.markdown("### 📊 Data Quality Audit Report")
        q_col1, q_col2, q_col3, q_col4 = st.columns(4)

        score_color = "#34D399" if report.quality_score >= 80 else ("#FBBF24" if report.quality_score >= 60 else "#FB7185")
        q_col1.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-title">Overall Quality Score</div>
                <div class="metric-val" style="color: {score_color};">{report.quality_score:.1f} / 100</div>
                <div class="metric-sub">Cleanliness & Hygiene</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        q_col2.metric("Total Rows / Columns", f"{report.total_rows:,} rows / {report.total_columns} cols")
        q_col3.metric("Missing Cells", f"{report.missing_cells:,} ({report.missing_percentage:.1f}%)")
        q_col4.metric("Duplicate Rows", f"{report.duplicate_rows:,}")

        # Outlier & constant column alerts
        if report.constant_columns:
            st.warning(f"⚠️ Constant columns detected (zero variance): {', '.join(report.constant_columns)}")

        if report.outlier_counts:
            outlier_info = [f"**{col}:** {cnt} outliers" for col, cnt in report.outlier_counts.items() if cnt > 0]
            if outlier_info:
                st.info(f"ℹ️ IQR Outliers detected: {', '.join(outlier_info)}")

        # Data preview
        st.markdown("#### 👁️ Dataset Preview (First 5 Rows)")
        st.dataframe(df.head(5), use_container_width=True)

        if st.button("💾 Confirm & Ingest Dataset into Catalog", type="primary"):
            save_path = Path(settings.dataset_dir) / f"{uuid.uuid4()}_{safe_name}"
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(content)

            dataset = Dataset(
                id=uuid.uuid4(),
                name=safe_name,
                source="user_upload",
                description=f"User imported dataset ({report.total_rows} rows)",
                file_path=str(save_path),
                row_count=report.total_rows,
                column_count=report.total_columns,
                columns_json=json.dumps(list(df.columns)),
                quality_report_json=json.dumps(report.model_dump()),
                is_active=True,
            )
            db.add(dataset)
            db.flush()

            ver = DatasetVersion(id=uuid.uuid4(), dataset_id=dataset.id, version=1, row_count=report.total_rows)
            db.add(ver)
            db.commit()

            st.success("Dataset successfully ingested and indexed!")
            st.rerun()

    except Exception as exc:
        st.error(f"Validation or parsing error: {exc}")

st.markdown("---")
st.markdown("### 🗄️ Registered Datasets Catalog")
datasets = db.query(Dataset).filter(Dataset.is_active.is_(True)).all()

if datasets:
    cat_rows = []
    for d in datasets:
        q_score_str = "N/A"
        if d.quality_report_json:
            try:
                rep = json.loads(d.quality_report_json)
                q_score_str = f"{rep.get('quality_score', 0):.1f}%"
            except Exception:
                pass
        cat_rows.append({
            "Dataset Name": d.name,
            "Source": d.source.upper(),
            "Rows": d.row_count,
            "Columns": d.column_count,
            "Quality Score": q_score_str,
            "Imported On": d.created_at.strftime("%Y-%m-%d"),
        })
    st.dataframe(pd.DataFrame(cat_rows), use_container_width=True)
else:
    st.info("No datasets registered yet.")

db.close()
