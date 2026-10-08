"""Dataset management and upload validation endpoints."""

from __future__ import annotations

import io
import json
import uuid
from pathlib import Path
from typing import List

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.config import get_settings
from app.db.models.dataset import Dataset, DatasetVersion
from app.db.models.user import User
from app.ml.data_quality import assess_data_quality
from app.schemas.dataset import DataQualityReport, DatasetResponse
from app.security.file_validator import validate_uploaded_file
from app.utils.errors import EntityNotFoundError

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.get("", response_model=List[DatasetResponse])
def list_datasets(db: Session = Depends(get_db)):
    """List available training and benchmark datasets."""
    datasets = db.execute(select(Dataset).where(Dataset.is_active.is_(True))).scalars().all()
    results = []
    for d in datasets:
        q_score = None
        if d.quality_report_json:
            try:
                rep = json.loads(d.quality_report_json)
                q_score = rep.get("quality_score")
            except Exception:
                pass
        resp = DatasetResponse(
            id=d.id,
            name=d.name,
            source=d.source,
            description=d.description,
            row_count=d.row_count,
            column_count=d.column_count,
            is_active=d.is_active,
            created_at=d.created_at,
            quality_score=q_score,
        )
        results.append(resp)
    return results


@router.post("/upload", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload software project historical CSV dataset with automatic quality assessment."""
    settings = get_settings()
    content = await file.read()

    safe_name, ext = validate_uploaded_file(file.filename or "upload.csv", content)

    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not parse CSV file: {exc}",
        )

    # Assess quality
    quality_report = assess_data_quality(df)

    # Save to disk
    save_path = Path(settings.dataset_dir) / f"{uuid.uuid4()}_{safe_name}"
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(content)

    # Save to database
    dataset = Dataset(
        id=uuid.uuid4(),
        name=safe_name,
        source="user_upload",
        description=f"User uploaded dataset ({len(df)} rows, {len(df.columns)} columns)",
        file_path=str(save_path),
        row_count=len(df),
        column_count=len(df.columns),
        columns_json=json.dumps(list(df.columns)),
        quality_report_json=json.dumps(quality_report.model_dump()),
        is_active=True,
    )
    db.add(dataset)
    db.flush()

    version = DatasetVersion(
        id=uuid.uuid4(),
        dataset_id=dataset.id,
        version=1,
        row_count=len(df),
    )
    db.add(version)
    db.commit()
    db.refresh(dataset)

    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        source=dataset.source,
        description=dataset.description,
        row_count=dataset.row_count,
        column_count=dataset.column_count,
        is_active=dataset.is_active,
        created_at=dataset.created_at,
        quality_score=quality_report.quality_score,
    )


@router.get("/{dataset_id}/quality", response_model=DataQualityReport)
def get_dataset_quality(dataset_id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve full data quality audit for a dataset."""
    dataset = db.execute(select(Dataset).where(Dataset.id == dataset_id)).scalar_one_or_none()
    if not dataset:
        raise EntityNotFoundError("Dataset", dataset_id)

    if dataset.quality_report_json:
        data = json.loads(dataset.quality_report_json)
        return DataQualityReport.model_validate(data)

    if dataset.file_path and Path(dataset.file_path).exists():
        df = pd.read_csv(dataset.file_path)
        report = assess_data_quality(df)
        dataset.quality_report_json = json.dumps(report.model_dump())
        db.commit()
        return report

    raise HTTPException(status_code=404, detail="Quality report not available for this dataset.")
