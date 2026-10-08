"""ORM models package.

Import all models here so Alembic can discover them for auto-generation.
"""

from app.db.models.user import User, Organization  # noqa: F401
from app.db.models.project import Project, ProjectScope  # noqa: F401
from app.db.models.work_item import WorkItem, Dependency  # noqa: F401
from app.db.models.estimate import Estimate, EstimateComponent  # noqa: F401
from app.db.models.scenario import Scenario  # noqa: F401
from app.db.models.assumption import Assumption  # noqa: F401
from app.db.models.risk import Risk  # noqa: F401
from app.db.models.dataset import Dataset, DatasetVersion  # noqa: F401
from app.db.models.model_registry import ModelVersion  # noqa: F401
from app.db.models.audit_log import AuditLog  # noqa: F401
from app.db.models.integration import Integration  # noqa: F401
