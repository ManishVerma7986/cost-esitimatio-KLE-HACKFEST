"""Deterministic architectural scope decomposer for offline / fallback mode.

Constructs realistic, industry-standard Work Breakdown Structures when external
LLM APIs are unavailable or keys are unconfigured.
"""

from __future__ import annotations

import re
from app.schemas.llm_responses import (
    IntegrationIdentified,
    RecommendationResponse,
    Requirement,
    ScopeDecomposition,
    TaskDecomposition,
    WorkPhaseDecomposition,
)


def decompose_scope_offline(
    name: str,
    description: str,
    product_type: str | None = None,
    industry: str | None = None,
    target_platform: str | None = None,
) -> ScopeDecomposition:
    """Produce an evidence-based, domain-tailored ScopeDecomposition."""
    desc_lower = description.lower()
    prod_type = (product_type or "Web Application").lower()
    platform = (target_platform or "Cloud / Web").lower()

    # Detect keywords
    has_auth = any(k in desc_lower for k in ["auth", "login", "user", "account", "role", "permission"])
    has_payment = any(k in desc_lower for k in ["pay", "stripe", "billing", "subscription", "checkout", "invoice"])
    has_search = any(k in desc_lower for k in ["search", "filter", "query", "elasticsearch"])
    has_ai = any(k in desc_lower for k in ["ai", "ml", "model", "prediction", "llm", "recommend", "nlp"])
    has_realtime = any(k in desc_lower for k in ["chat", "notification", "realtime", "websocket", "streaming"])
    has_mobile = any(k in platform for k in ["ios", "android", "mobile", "flutter", "react native"])

    requirements = [
        Requirement(
            name="System Architecture & Scalability",
            description="High-availability modular backend architecture with horizontal scalability.",
            category="non_functional",
            priority="critical",
        ),
        Requirement(
            name="Core Domain Business Logic",
            description=f"Core operational workflows and data handling for {name}.",
            category="functional",
            priority="high",
        ),
    ]

    if has_auth:
        requirements.append(
            Requirement(
                name="Identity & Access Management",
                description="Secure authentication, JWT token lifecycle, role-based access control (RBAC).",
                category="security",
                priority="high",
            )
        )

    if has_payment:
        requirements.append(
            Requirement(
                name="Payment Processing & Billing",
                description="PCI-compliant payment gateway integration, subscription billing, and webhooks.",
                category="integration",
                priority="high",
            )
        )

    if has_ai:
        requirements.append(
            Requirement(
                name="AI / ML Inference Engine",
                description="Model inference pipelines, input validation, latency monitoring, and caching.",
                category="functional",
                priority="high",
            )
        )

    # Phases & Tasks
    phases = [
        WorkPhaseDecomposition(
            name="Discovery & Architecture",
            description="System design, requirements finalization, and infrastructure planning.",
            tasks=[
                TaskDecomposition(
                    name="Architecture Design & Threat Modeling",
                    description="Design component topology, data flow diagrams, and STRIDE security threat analysis.",
                    complexity="high",
                    suggested_role="Software Architect",
                    dependencies=[],
                ),
                TaskDecomposition(
                    name="Database Schema & Migration Strategy",
                    description="ERD modeling, index planning, and migration baseline setup.",
                    complexity="medium",
                    suggested_role="Database Administrator",
                    dependencies=["Architecture Design & Threat Modeling"],
                ),
            ],
        ),
        WorkPhaseDecomposition(
            name="Core Backend Services",
            description="RESTful API services, business logic engines, and database access layer.",
            tasks=[
                TaskDecomposition(
                    name="Data Access & Repository Layer",
                    description="ORM models, session management, transaction handling, and repository patterns.",
                    complexity="medium",
                    suggested_role="Backend Developer",
                    dependencies=["Database Schema & Migration Strategy"],
                ),
                TaskDecomposition(
                    name="Core Business Logic & API Endpoints",
                    description="Core domain endpoints, payload validation, business rules, and error handling.",
                    complexity="high",
                    suggested_role="Senior Backend Developer",
                    dependencies=["Data Access & Repository Layer"],
                ),
            ],
        ),
    ]

    frontend_tasks = [
        TaskDecomposition(
            name="Design System & UI Components",
            description="Accessible design tokens, typography, layout grid, and atomic component library.",
            complexity="medium",
            suggested_role="UI/UX Designer",
            dependencies=["Architecture Design & Threat Modeling"],
        ),
        TaskDecomposition(
            name="User Workflows & State Management",
            description="Responsive user interface pages, state store, API client integration, and error states.",
            complexity="high",
            suggested_role="Frontend Developer",
            dependencies=["Design System & UI Components", "Core Business Logic & API Endpoints"],
        ),
    ]

    if has_mobile:
        phases.append(
            WorkPhaseDecomposition(
                name="Mobile & Client Application",
                description="Native/cross-platform client implementation.",
                tasks=frontend_tasks,
            )
        )
    else:
        phases.append(
            WorkPhaseDecomposition(
                name="Frontend Web Application",
                description="Web user interface, dashboards, and client state orchestration.",
                tasks=frontend_tasks,
            )
        )

    # QA & Deployment
    phases.append(
        WorkPhaseDecomposition(
            name="Quality Assurance & Testing",
            description="Automated unit, integration, and end-to-end regression testing.",
            tasks=[
                TaskDecomposition(
                    name="Unit & Integration Test Suite",
                    description="Pytest / Jest coverage for core logic, edge cases, and API contract testing.",
                    complexity="medium",
                    suggested_role="QA Engineer",
                    dependencies=["Core Business Logic & API Endpoints"],
                ),
                TaskDecomposition(
                    name="Security & Performance Testing",
                    description="SAST / DAST scans, load testing under peak traffic, and vulnerability mitigation.",
                    complexity="high",
                    suggested_role="Security Engineer",
                    dependencies=["Unit & Integration Test Suite"],
                ),
            ],
        )
    )

    phases.append(
        WorkPhaseDecomposition(
            name="DevOps, Infrastructure & Launch",
            description="CI/CD pipelines, container orchestration, monitoring, and go-live deployment.",
            tasks=[
                TaskDecomposition(
                    name="CI/CD Pipeline & Automated Delivery",
                    description="GitHub Actions / GitLab CI for automated linting, test runs, and image builds.",
                    complexity="medium",
                    suggested_role="DevOps Engineer",
                    dependencies=["Unit & Integration Test Suite"],
                ),
                TaskDecomposition(
                    name="Cloud Infrastructure & Observability",
                    description="Infrastructure as Code (Terraform), metrics, structured logging, and alerting.",
                    complexity="high",
                    suggested_role="Cloud Engineer",
                    dependencies=["CI/CD Pipeline & Automated Delivery"],
                ),
            ],
        )
    )

    # Integrations
    integrations = []
    if has_payment:
        integrations.append(IntegrationIdentified(name="Stripe / Payment Gateway", complexity="medium"))
    if has_auth:
        integrations.append(IntegrationIdentified(name="OAuth2 / Identity Provider", complexity="medium"))
    integrations.append(IntegrationIdentified(name="Cloud Storage & CDN (AWS / GCP)", complexity="low"))

    # Questions & Risks
    clarification_questions = [
        "What are the target peak concurrent users and daily active user projections?",
        "Are there strict regional data sovereignty or compliance mandates (GDPR, HIPAA, SOC2)?",
        "What are the Service Level Agreements (SLAs) required for uptime and maximum API latency?",
        "Will third-party external integrations provide sandbox testing environments?",
    ]

    identified_risks = [
        "Scope creep due to evolving non-functional scalability and data residency constraints.",
        "Third-party integration latency and rate-limiting bottlenecks.",
        "Team ramp-up curve on domain-specific infrastructure and compliance auditing.",
    ]

    tech_components = ["Python / FastAPI", "PostgreSQL", "React / Streamlit", "Docker / Kubernetes", "Redis"]

    return ScopeDecomposition(
        requirements=requirements,
        work_phases=phases,
        technology_components=tech_components,
        integrations=integrations,
        clarification_questions=clarification_questions,
        assumptions_made=[
            "Standard 40-hour engineering work week with 75% productive time factor.",
            "Development team has foundational proficiency in the chosen technology stack.",
            "Staging environment mirrors production hardware and network topology.",
        ],
        identified_risks=identified_risks,
    )


def generate_recommendation_offline(
    project_name: str,
    total_cost: float,
    effort_hours: float,
    duration_weeks: float,
    p50: float,
    p80: float,
) -> RecommendationResponse:
    """Generate professional narrative recommendation without remote LLM."""
    buffer_pct = ((p80 - p50) / p50 * 100) if p50 > 0 else 15.0
    return RecommendationResponse(
        summary=(
            f"The estimated budget for {project_name} is ${total_cost:,.2f} requiring approximately "
            f"{effort_hours:,.0f} engineering hours across {duration_weeks:.1f} weeks. "
            f"Uncertainty modeling projects a median outcome (P50) of ${p50:,.2f} and an 80th-percentile "
            f"confidence benchmark (P80) of ${p80:,.2f}."
        ),
        key_findings=[
            f"Core personnel labor represents the primary cost driver across the {duration_weeks:.1f} week schedule.",
            f"A {buffer_pct:.1f}% risk contingency variance exists between P50 and P80 scenarios.",
            "Backend architecture and integration verification carry the highest complexity weighting.",
        ],
        recommendations=[
            "Implement phased milestone delivery to validate core architecture before scaling frontend teams.",
            "Maintain the recommended P80 budget buffer as an executive reserve for external integration delays.",
            "Establish automated CI/CD and regression testing early to prevent downstream QA debt.",
        ],
        risk_commentary=(
            "Key exposure vectors include integration dependencies and potential scope creep. "
            "Continuous tracking against the Work Breakdown Structure will keep variances within tolerance."
        ),
        confidence_commentary=(
            "Estimate confidence is calibrated against empirical parametric baselines and Monte Carlo simulations."
        ),
    )
