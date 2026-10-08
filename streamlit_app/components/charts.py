"""Plotly chart components with unified dark visual aesthetics."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go


def plot_cost_breakdown_donut(cost_breakdown: dict) -> go.Figure:
    """Create a sleek donut chart of the project cost breakdown."""
    labels = ["Personnel Labor", "Tooling & SaaS", "Cloud Infrastructure", "Contingency Buffer"]
    values = [
        float(cost_breakdown.get("personnel", 0)),
        float(cost_breakdown.get("tooling", 0)),
        float(cost_breakdown.get("cloud", 0)),
        float(cost_breakdown.get("contingency", 0)),
    ]

    colors = ["#38BDF8", "#818CF8", "#34D399", "#FBBF24"]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.62,
                marker=dict(colors=colors, line=dict(color="#0A0E17", width=2)),
                textinfo="percent+label",
                textposition="outside",
                hoverinfo="label+value+percent",
            )
        ]
    )

    total_cost = sum(values)
    fig.update_layout(
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=30, b=30, l=30, r=30),
        annotations=[
            dict(
                text=f"Total<br><b>${total_cost:,.0f}</b>",
                x=0.5,
                y=0.5,
                font_size=16,
                font_family="Plus Jakarta Sans",
                font_color="#F8FAFC",
                showarrow=False,
            )
        ],
    )
    return fig


def plot_monte_carlo_distribution(
    p10: float, p50: float, p80: float, p90: float, mean_val: float
) -> go.Figure:
    """Plot Monte Carlo probability density curve with P10/P50/P80 percentile milestones."""
    # Synthetic normal-skew curve centered on P50 for smooth visual S-curve
    std = max(100.0, (p90 - p10) / 2.56)
    x = np.linspace(max(0, p10 - std), p90 + std, 300)
    y = (1 / (std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - p50) / std) ** 2)

    fig = go.Figure()

    # Fill area under curve
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="lines",
            line=dict(color="#38BDF8", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(56, 189, 248, 0.15)",
            name="Simulated Distribution",
        )
    )

    # Vertical percentile markers
    milestones = [
        ("P10", p10, "#94A3B8"),
        ("P50 (Median)", p50, "#34D399"),
        ("P80 (Target)", p80, "#FBBF24"),
        ("P90", p90, "#FB7185"),
    ]

    for label, val, col in milestones:
        fig.add_vline(
            x=val,
            line_dash="dash",
            line_color=col,
            line_width=1.8,
            annotation_text=f"{label}: ${val:,.0f}",
            annotation_position="top right",
            annotation_font=dict(color=col, size=11),
        )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=40, b=30, l=40, r=40),
        xaxis=dict(
            title="Total Cost ($ USD)",
            color="#94A3B8",
            gridcolor="rgba(255,255,255,0.05)",
            tickformat="$,.0f",
        ),
        yaxis=dict(showticklabels=False, gridcolor="rgba(255,255,255,0.05)"),
        showlegend=False,
    )
    return fig


def plot_scenario_comparison_bars(scenarios_data: list[dict]) -> go.Figure:
    """Plot grouped comparative bar chart for what-if scenarios."""
    names = [s["name"] for s in scenarios_data]
    totals = [float(s.get("total_cost", 0)) for s in scenarios_data]
    p80s = [float(s.get("p80", 0) or 0) for s in scenarios_data]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Estimated Total Cost",
            x=names,
            y=totals,
            marker_color="#38BDF8",
        )
    )
    fig.add_trace(
        go.Bar(
            name="P80 High-Confidence Reserve",
            x=names,
            y=p80s,
            marker_color="#FBBF24",
        )
    )

    fig.update_layout(
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=30, b=30, l=40, r=40),
        xaxis=dict(color="#94A3B8", gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(color="#94A3B8", gridcolor="rgba(255,255,255,0.05)", tickformat="$,.0f"),
        legend=dict(font=dict(color="#E2E8F0")),
    )
    return fig
