import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from execution.projects_service import get_published_projects, get_project_by_id
from execution.reports_service import get_resident_reports
from execution.ai_service import ask_project_assistant, ask_general_assistant, test_gemini_connection
from execution.env_config import GEMINI_API_KEY, GEMINI_MODEL
from ui.nav import render_sidebar
from ui.components import render_header, render_pilot_notice, get_status_badge_html, get_provenance_badge_html

st.set_page_config(page_title="AI Civic Assistant — CivicSync", page_icon="🤖", layout="wide")
render_sidebar()
render_header("AI Civic & Disruption Assistant", "Context-grounded guidance for personal complaints, neighbourhood proximity, and public works")
render_pilot_notice()

user = st.session_state.get("auth_user")
profile = st.session_state.get("auth_profile") or {}
access_token = st.session_state.get("access_token")
user_id = user.get("user_id") if isinstance(user, dict) else (user.id if user else None)
home_lat = profile.get("home_latitude")
home_lon = profile.get("home_longitude")

projects = get_published_projects(access_token=access_token)

if not projects:
    st.info("No registered projects available to inspect. Seed demo projects or check back later.")
    st.stop()

# ------------------------------------------------------------------
# Scope Selection: General Assistant vs Specific Project
# ------------------------------------------------------------------
SCOPE_GENERAL = "🌐 General Civic Assistant (My Reports, Proximity & City Works)"
project_lookup = {f"🏗️ Project: {p.get('title')} ({p.get('location_name')})": p.get("id") for p in projects}
all_scopes = [SCOPE_GENERAL] + list(project_lookup.keys())

default_idx = 0
selected_id = st.session_state.get("selected_project_id")
if selected_id:
    for idx, (label, pid) in enumerate(project_lookup.items()):
        if pid == selected_id:
            default_idx = idx + 1
            break

col_scope, col_stat = st.columns([2.2, 1.0])
with col_scope:
    chosen_scope = st.selectbox(
        "Assistant Inquiry Scope",
        all_scopes,
        index=default_idx,
        help="Select General Assistant to ask about your complaints and home proximity, or pick a specific public work."
    )

with col_stat:
    if GEMINI_API_KEY:
        st.success(f"🟢 Gemini Active: `{GEMINI_MODEL}`")
    else:
        st.info("ℹ️ **Deterministic Mode** (API key not set — displaying verified facts)")

is_general_mode = (chosen_scope == SCOPE_GENERAL)

# ------------------------------------------------------------------
# Context Card: General Citizen Profile vs Project Dossier
# ------------------------------------------------------------------
preset_question = None

if is_general_mode:
    st.session_state["selected_project_id"] = None
    u_name = profile.get("display_name", "Resident")
    u_role = profile.get("role", "RESIDENT")
    
    my_reports = get_resident_reports(user_id, access_token) if user_id else []
    total_reps = len(my_reports)
    res_reps = len([r for r in my_reports if r.get("status") == "RESOLVED"])

    loc_str = f"📍 Saved Neighbourhood: **{home_lat:.4f}, {home_lon:.4f}** (Proximity features active)" if (home_lat and home_lon) else "📍 Home Location: *Not set yet (Drop pin on Home or Explore Map)*"

    st.markdown(f"""
    <div class="civic-card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="font-size:12px; font-weight:700; color:#167D70;">👤 RESIDENT CIVIC CONTEXT</span>
            <span style="font-size:12px; color:#64748B;">Role: <strong>{u_role}</strong></span>
        </div>
        <h4 style="margin:2px 0 4px 0; color:#172B4D;">Civic Assistant for {u_name}</h4>
        <div style="font-size:13px; color:#475569; margin-bottom:8px;">{loc_str}</div>
        <div style="display:flex; gap:20px; font-size:13px; background:#F8FAFC; padding:8px 12px; border-radius:6px; border:1px solid #E2E8F0;">
            <div>📋 <strong>My Reports Filed:</strong> {total_reps}</div>
            <div>✅ <strong>Resolved:</strong> {res_reps}</div>
            <div>🏗️ <strong>Active City Projects:</strong> {len(projects)}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Ask a Question")
    st.markdown("##### Quick Shortcuts:")
    col_g1, col_g2, col_g3, col_g4 = st.columns(4)
    with col_g1:
        if st.button("📋 My Reports Status", use_container_width=True):
            preset_question = "How many reports have I complained and how many are solved?"
    with col_g2:
        if st.button("📍 Nearest Work Distance", use_container_width=True):
            preset_question = "How much from my home is the nearest public work?"
    with col_g3:
        if st.button("⚠️ Works Within 5 km", use_container_width=True):
            preset_question = "What public infrastructure works are within 5 km of my home?"
    with col_g4:
        if st.button("🏛️ Active City Works", use_container_width=True):
            preset_question = "What are the most active public infrastructure projects across Chennai right now?"

    placeholder_txt = "e.g. How many complaints have I filed, or how far from my home is the nearest roadwork?"

else:
    active_project_id = project_lookup[chosen_scope]
    st.session_state["selected_project_id"] = active_project_id

    proj = get_project_by_id(active_project_id, access_token=access_token)
    if proj:
        p_title = proj.get("title")
        p_status = proj.get("status")
        p_org = proj.get("organizations", {}).get("name") if isinstance(proj.get("organizations"), dict) else "Public Authority"
        p_end = proj.get("current_estimated_end_date")
        p_disruption = proj.get("expected_disruption") or "No lane disruption logged."
        p_origin = proj.get("data_origin")

        st.markdown(f"""
        <div class="civic-card">
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                <div>{get_provenance_badge_html(p_origin)}</div>
                <div>{get_status_badge_html(p_status)}</div>
            </div>
            <h4 style="margin: 4px 0; color: #172B4D;">{p_title}</h4>
            <p style="margin: 2px 0; color: #64748B;">🏛️ <strong>Managing Body:</strong> {p_org} | 🎯 <strong>Target Completion:</strong> {p_end}</p>
            <p style="margin: 4px 0; font-size: 0.9rem; color: #DC2626;">⚠️ <strong>Advisory:</strong> {p_disruption}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### Ask a Question")
    st.markdown("##### Quick Shortcuts:")
    col_q1, col_q2, col_q3 = st.columns(3)
    with col_q1:
        if st.button("When is work estimated to finish?", use_container_width=True):
            preset_question = "When is this work estimated to complete and are there any recorded delays?"
    with col_q2:
        if st.button("What are the lane closures?", use_container_width=True):
            preset_question = "What is the recorded traffic disruption and road restriction for this project?"
    with col_q3:
        if st.button("What was the latest official update?", use_container_width=True):
            preset_question = "Who is the managing authority and what was the latest recorded progress update?"

    placeholder_txt = "e.g. Is traffic diverted through alternate streets?"

# ------------------------------------------------------------------
# Question Input & Submission
# ------------------------------------------------------------------
user_query = st.text_input(
    "Type your question:",
    value=preset_question if preset_question else "",
    placeholder=placeholder_txt
)

if st.button("Submit Question", use_container_width=True, type="primary") or preset_question:
    if not user_query.strip():
        st.error("Please enter a question or click a prompt shortcut.")
    else:
        with st.spinner("Analyzing verified civic facts and generating grounded response..."):
            if is_general_mode:
                answer = ask_general_assistant(
                    user_query,
                    user_id=user_id,
                    profile=profile,
                    access_token=access_token
                )
            else:
                answer = ask_project_assistant(
                    active_project_id,
                    user_query,
                    access_token=access_token
                )

            with st.container(border=True):
                st.markdown("#### 🤖 Grounded Civic Advisory")
                st.markdown(answer)
                st.divider()
                st.caption("🛡️ **Fact-Grounded Response:** Answers are strictly constrained by verified database records and proximity calculations. The assistant does not invent official closures or safety assurances.")
