import streamlit as st
from execution.auth_service import sign_in_demo
from ui.styles import GLOBAL_CSS

def init_session_state():
    """Initializes isolated session state variables for the active user tab."""
    if "auth_user" not in st.session_state:
        st.session_state["auth_user"] = None
    if "auth_profile" not in st.session_state:
        st.session_state["auth_profile"] = None
    if "auth_membership" not in st.session_state:
        st.session_state["auth_membership"] = None
    if "access_token" not in st.session_state:
        st.session_state["access_token"] = None
    if "selected_project_id" not in st.session_state:
        st.session_state["selected_project_id"] = None

def render_sidebar():
    """Renders the common role-aware sidebar navigation and authentication state."""
    init_session_state()
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("""
        <div class="sidebar-brand">
            <h2>CivicSync</h2>
            <small>Chennai Public Works &amp; Disruption Platform</small>
        </div>
        """, unsafe_allow_html=True)

        user = st.session_state.get("auth_user")
        profile = st.session_state.get("auth_profile")
        membership = st.session_state.get("auth_membership")

        if user and profile:
            role = profile.get("role", "RESIDENT")
            name = profile.get("display_name", "User")

            st.markdown(f"**Signed in as:** `{name}`")
            if role == "RESIDENT":
                st.caption("Role: Resident Citizen")
            elif role == "AUTHORITY":
                org_name = membership.get("organizations", {}).get("name") if membership else "Public Authority"
                st.caption(f"Authority: {org_name}")
            elif role == "ADMIN":
                st.caption("Role: Platform Administrator")

            if st.button("Sign Out", key="sidebar_logout_btn", use_container_width=True):
                st.session_state["auth_user"] = None
                st.session_state["auth_profile"] = None
                st.session_state["auth_membership"] = None
                st.session_state["access_token"] = None
                st.session_state["selected_project_id"] = None
                st.rerun()
        else:
            st.info("Browsing as Guest. Sign in on the Home page or choose a Demo account below.")

            st.markdown("### Demo")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Resident", key="demo_btn_res", use_container_width=True):
                    _switch_demo("RESIDENT")
                if st.button("GCC Roads", key="demo_btn_gcc", use_container_width=True):
                    _switch_demo("AUTHORITY_GCC")
            with col2:
                if st.button("Metro Water", key="demo_btn_cmwssb", use_container_width=True):
                    _switch_demo("AUTHORITY_CMWSSB")
                if st.button("Admin", key="demo_btn_admin", use_container_width=True):
                    _switch_demo("ADMIN")

        st.divider()
        st.markdown("### Navigation")
        st.markdown("""
        - **Explore Map** — Active works & disruptions
        - **Report Issue** — File citizen problem reports
        - **My Reports** — Track status & authority notes
        - **AI Assistant** — Grounded Q&A on projects
        - **Authority Portal** — Register works & triage
        - **Admin Portal** — Organization approvals
        """)

        st.caption("CivicSync · Version 1.0")

def _switch_demo(persona_key: str):
    """Handles one-click demo login from sidebar."""
    success, msg, session_data = sign_in_demo(persona_key)
    if success and session_data:
        st.session_state["auth_user"] = session_data
        st.session_state["auth_profile"] = session_data.get("profile")
        st.session_state["auth_membership"] = session_data.get("membership")
        st.session_state["access_token"] = session_data.get("access_token")
        st.success(f"Switched to {persona_key}!")
        st.rerun()
    else:
        st.error(f"Demo sign-in failed: {msg}")

