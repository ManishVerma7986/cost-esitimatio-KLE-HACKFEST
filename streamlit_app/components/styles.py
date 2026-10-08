"""Custom CSS design tokens and glassmorphic styling for Streamlit."""

import streamlit as st


def apply_custom_css():
    """Inject premium CSS styling."""
    st.markdown(
        """
        <style>
        /* Import Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', sans-serif;
        }

        /* Glassmorphic card styling */
        .glass-card {
            background: rgba(19, 27, 42, 0.75);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 22px;
            margin-bottom: 18px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            transition: all 0.25s ease;
        }
        .glass-card:hover {
            border-color: rgba(0, 210, 255, 0.25);
            box-shadow: 0 8px 32px 0 rgba(0, 210, 255, 0.12);
        }

        /* Metric cards */
        .metric-container {
            background: linear-gradient(135deg, rgba(20, 30, 48, 0.8), rgba(36, 59, 85, 0.5));
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 16px 20px;
            margin: 6px 0;
        }
        .metric-title {
            color: #94A3B8;
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-weight: 600;
        }
        .metric-val {
            color: #F8FAFC;
            font-size: 1.85rem;
            font-weight: 700;
            margin-top: 4px;
        }
        .metric-sub {
            color: #38BDF8;
            font-size: 0.8rem;
            margin-top: 2px;
        }

        /* Badges */
        .badge-cyan {
            background: rgba(0, 210, 255, 0.15);
            color: #38BDF8;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-block;
            border: 1px solid rgba(56, 189, 248, 0.3);
        }
        .badge-emerald {
            background: rgba(16, 185, 129, 0.15);
            color: #34D399;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-block;
            border: 1px solid rgba(52, 211, 153, 0.3);
        }
        .badge-amber {
            background: rgba(245, 158, 11, 0.15);
            color: #FBBF24;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-block;
            border: 1px solid rgba(251, 191, 36, 0.3);
        }
        .badge-rose {
            background: rgba(244, 63, 94, 0.15);
            color: #FB7185;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-block;
            border: 1px solid rgba(251, 113, 133, 0.3);
        }

        /* Custom headers */
        .hero-title {
            background: linear-gradient(90deg, #FFFFFF, #93C5FD, #38BDF8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.3rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin-bottom: 6px;
        }
        .hero-subtitle {
            color: #94A3B8;
            font-size: 1.05rem;
            margin-bottom: 24px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
