import streamlit as st
from typing import Dict, Any, Optional

def render_header(title: str = "CivicSync", subtitle: str = "Understand public works. Navigate disruptions. Improve civic accountability."):
    """Renders the top branding header."""
    st.markdown(f"""
    <div class="civic-header">
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def render_pilot_notice():
    """Previously rendered pilot notice banner. Now disabled per UI cleanup."""
    pass

def get_status_badge_html(status: str) -> str:
    """Generates styled HTML badge for project and report statuses."""
    s = (status or "").upper()
    css_class = "badge-in-progress"

    if s in ["COMPLETED", "RESOLVED"]:
        css_class = "badge-completed"
    elif s in ["PLANNED"]:
        css_class = "badge-planned"
    elif s in ["DELAYED", "REJECTED"]:
        css_class = "badge-delayed"
    elif s in ["ACKNOWLEDGED"]:
        css_class = "badge-acknowledged"
    elif s in ["PENDING_REVIEW", "PENDING"]:
        css_class = "badge-pending"

    display_label = s.replace("_", " ")
    return f'<span class="badge-status {css_class}">{display_label}</span>'

def get_provenance_badge_html(origin: str) -> str:
    """Generates explicit data provenance badge to prevent deceptive demo data."""
    o = (origin or "").upper()
    if o == "DEMO_DATA":
        return '<span class="badge-demo">🔬 SIMULATED DEMO RECORD</span>'
    elif o == "CITIZEN_REPORTED":
        return '<span class="badge-status badge-pending">👥 CITIZEN OBSERVATION</span>'
    elif o == "ORGANIZATION_ENTERED":
        return '<span class="badge-official">🏛️ OFFICIAL REGISTERED WORK</span>'
    elif o == "PUBLIC_SOURCE_IMPORTED":
        return '<span class="badge-official">📋 PUBLIC SOURCE IMPORT</span>'
    return f'<span class="badge-demo">{o}</span>'

def render_kpi_metrics(metrics: list):
    """Renders a row of metric cards."""
    cols = st.columns(len(metrics))
    for idx, (label, val, delta) in enumerate(metrics):
        with cols[idx]:
            st.metric(label=label, value=val, delta=delta if delta else None)
