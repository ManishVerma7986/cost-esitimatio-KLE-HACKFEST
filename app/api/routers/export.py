"""Estimate export endpoints supporting JSON, CSV, Excel, and PDF."""

from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models.project import Project
from app.db.models.user import User
from app.services.estimate_service import get_estimate_response
from app.utils.errors import EntityNotFoundError
from app.utils.export import (
    export_estimate_csv,
    export_estimate_excel,
    export_estimate_json,
    export_estimate_pdf,
)

router = APIRouter(prefix="/estimates/{estimate_id}/export", tags=["Export"])


@router.get("/json")
def download_json(
    estimate_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download estimate as structured JSON."""
    estimate = get_estimate_response(db, estimate_id)
    project = db.execute(select(Project).where(Project.id == estimate.project_id)).scalar_one_or_none()
    proj_name = project.name if project else "Project"

    json_str = export_estimate_json(estimate, proj_name)
    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="estimate_{estimate_id}.json"'},
    )


@router.get("/csv")
def download_csv(
    estimate_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download itemized cost breakdown as CSV."""
    estimate = get_estimate_response(db, estimate_id)
    project = db.execute(select(Project).where(Project.id == estimate.project_id)).scalar_one_or_none()
    proj_name = project.name if project else "Project"

    csv_str = export_estimate_csv(estimate, proj_name)
    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="estimate_{estimate_id}.csv"'},
    )


@router.get("/excel")
def download_excel(
    estimate_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download styled multi-tab Excel spreadsheet."""
    estimate = get_estimate_response(db, estimate_id)
    project = db.execute(select(Project).where(Project.id == estimate.project_id)).scalar_one_or_none()
    proj_name = project.name if project else "Project"

    excel_bytes = export_estimate_excel(estimate, proj_name)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="estimate_{estimate_id}.xlsx"'},
    )


@router.get("/pdf")
def download_pdf(
    estimate_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download executive PDF estimation brief."""
    estimate = get_estimate_response(db, estimate_id)
    project = db.execute(select(Project).where(Project.id == estimate.project_id)).scalar_one_or_none()
    proj_name = project.name if project else "Project"

    pdf_bytes = export_estimate_pdf(estimate, proj_name)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="estimate_{estimate_id}.pdf"'},
    )
