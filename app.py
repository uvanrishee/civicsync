import streamlit as st
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from execution.env_config import is_supabase_configured, DEMO_CREDENTIALS
from execution.auth_service import sign_in_user, sign_up_user, sign_in_demo, save_home_location, reload_profile, resend_verification_email
from execution.projects_service import get_published_projects, get_all_organizations
from ui.nav import render_sidebar
from ui.components import render_header, render_pilot_notice, get_status_badge_html, get_provenance_badge_html
from ui.map_view import render_pin_drop_map

st.set_page_config(
    page_title="CivicSync — Chennai Public Works & Disruption Platform",
    page_icon="🚧",
    layout="wide",
    initial_sidebar_state="expanded"
)

render_sidebar()
render_header()
render_pilot_notice()

# Check Database Configuration
if not is_supabase_configured():
    st.warning("""
    ⚠️ **Supabase Configuration Needed**:
    Please configure `SUPABASE_URL` and `SUPABASE_ANON_KEY` in your `.env` file to connect to live database records.
    Refer to `directives/setup_database.md` for the database schema migration script.
    """)

# Main Content Layout — Dedicated Sign In & Registration Portal
user = st.session_state.get("auth_user")
profile = st.session_state.get("auth_profile")

if user and profile:
    # Authenticated Welcome View
    role = profile.get("role", "RESIDENT")
    name = profile.get("display_name", "User")
    membership = st.session_state.get("auth_membership")
    org_name = membership.get("organizations", {}).get("name") if membership else None

    # ── Home Location Modal (RESIDENT only, shown once per account) ──────────
    if role == "RESIDENT":
        has_home = profile.get("home_latitude") is not None
        skipped  = st.session_state.get("_location_modal_skipped", False)

        if not has_home and not skipped:
            @st.dialog("📍 Set Your Neighbourhood Location", width="large")
            def _location_modal():
                st.markdown(
                    "Help us personalise the map for you. **Click anywhere on the map below** "
                    "to place or move your neighbourhood pin, or choose a quick area:"
                )

                # Quick neighbourhood presets
                CHENNAI_PRESETS = {
                    "Anna Salai": (13.0604, 80.2496),
                    "T. Nagar": (13.0418, 80.2341),
                    "Guindy": (13.0067, 80.2025),
                    "Adyar": (13.0012, 80.2565),
                    "Velachery": (12.9815, 80.2180),
                    "OMR": (12.9360, 80.2290),
                }

                st.caption("Popular Chennai Areas:")
                cols_pre = st.columns(len(CHENNAI_PRESETS))
                for idx, (p_name, coords) in enumerate(CHENNAI_PRESETS.items()):
                    with cols_pre[idx]:
                        if st.button(p_name, key=f"pre_{p_name}", use_container_width=True):
                            st.session_state["_dropped_home_lat"] = coords[0]
                            st.session_state["_dropped_home_lon"] = coords[1]
                            st.rerun()

                cur_lat = st.session_state.get("_dropped_home_lat")
                cur_lon = st.session_state.get("_dropped_home_lon")

                pin_data = render_pin_drop_map(
                    center_lat=cur_lat if cur_lat is not None else 13.0400,
                    center_lon=cur_lon if cur_lon is not None else 80.2300,
                    pinned_lat=cur_lat,
                    pinned_lon=cur_lon,
                    height=320,
                    key="modal_pin_drop_map"
                )

                clicked = pin_data.get("last_clicked") if pin_data else None
                if clicked and clicked.get("lat") and clicked.get("lng"):
                    clat = round(float(clicked["lat"]), 5)
                    clon = round(float(clicked["lng"]), 5)
                    if clat != cur_lat or clon != cur_lon:
                        st.session_state["_dropped_home_lat"] = clat
                        st.session_state["_dropped_home_lon"] = clon
                        st.rerun()

                if cur_lat is not None and cur_lon is not None:
                    st.success(f"📌 **Pin placed at:** `{cur_lat:.4f}, {cur_lon:.4f}` — Click anywhere on the map to move it, or save below.")
                    col_save, col_skip = st.columns(2)
                    with col_save:
                        if st.button("💾 Save My Location", use_container_width=True, type="primary", key="save_loc_modal_btn"):
                            user_id = user.get("user_id") if isinstance(user, dict) else user.id
                            ok, msg = save_home_location(user_id, cur_lat, cur_lon)
                            if ok:
                                updated = reload_profile(user_id)
                                st.session_state["auth_profile"] = updated
                                st.session_state.pop("_dropped_home_lat", None)
                                st.session_state.pop("_dropped_home_lon", None)
                                st.success("Location saved! The map will now centre on your area.")
                                st.rerun()
                            else:
                                st.error(msg)
                    with col_skip:
                        if st.button("Skip for Now", use_container_width=True, key="skip_loc_modal_btn1"):
                            st.session_state["_location_modal_skipped"] = True
                            st.session_state.pop("_dropped_home_lat", None)
                            st.session_state.pop("_dropped_home_lon", None)
                            st.rerun()
                else:
                    st.info("👉 Click anywhere on the map above to drop your pin, or choose a popular area above.")
                    if st.button("Skip for Now", use_container_width=True, key="skip_loc_modal_btn2"):
                        st.session_state["_location_modal_skipped"] = True
                        st.rerun()

            _location_modal()

    with st.container(border=True):
        col_prof, col_btn = st.columns([3, 1], vertical_alignment="center")
        with col_prof:
            st.markdown(f"### Welcome back, {name}")
            if role == "RESIDENT":
                st.markdown("Account Type: **Resident Citizen** &nbsp;|&nbsp; Jurisdiction: **Chennai Metropolitan Area**")
            elif role == "AUTHORITY":
                st.markdown(f"Account Type: **Authority Officer** &nbsp;|&nbsp; Department: **{org_name or 'Public Works Authority'}**")
            elif role == "ADMIN":
                st.markdown("Account Type: **Platform Administrator** &nbsp;|&nbsp; Access: **Full Governance Clearance**")
        with col_btn:
            if st.button("Sign Out", key="dash_signout_btn", use_container_width=True):
                st.session_state["auth_user"] = None
                st.session_state["auth_profile"] = None
                st.session_state["auth_membership"] = None
                st.session_state["access_token"] = None
                st.session_state["selected_project_id"] = None
                st.rerun()

    st.markdown("### Platform Workspaces & Services")

    # Balanced 4-Column Action Grid Tailored by Role
    col1, col2, col3, col4 = st.columns(4)

    if role == "RESIDENT":
        with col1:
            with st.container(border=True):
                st.markdown("#### 🗺️ Corridor Map")
                st.caption("Explore active roadworks, pipelines, metro lines, and traffic barricades.")
                if st.button("Open Map", key="res_btn_map", use_container_width=True):
                    st.switch_page("pages/1_Explore_Map.py")

        with col2:
            with st.container(border=True):
                st.markdown("#### 📢 Report Issue")
                st.caption("File potholes, open trenches, or water leaks with photo evidence.")
                if st.button("Report Issue", key="res_btn_rep", use_container_width=True):
                    st.switch_page("pages/2_Report_Issue.py")

        with col3:
            with st.container(border=True):
                st.markdown("#### 📋 My Reports")
                st.caption("Track real-time resolution status and official authority responses.")
                if st.button("My Reports", key="res_btn_myrep", use_container_width=True):
                    st.switch_page("pages/3_My_Reports.py")

        with col4:
            with st.container(border=True):
                st.markdown("#### 🤖 AI Assistant")
                st.caption("Grounded natural language answers on schedules and diversions.")
                if st.button("Ask Assistant", key="res_btn_ai", use_container_width=True):
                    st.switch_page("pages/4_AI_Assistant.py")

    elif role == "AUTHORITY":
        with col1:
            with st.container(border=True):
                st.markdown("#### 🏛️ Works Registry")
                st.caption("Register new public works and publish timeline updates.")
                if st.button("Manage Works", key="auth_btn_works", use_container_width=True):
                    st.switch_page("pages/5_Authority_Portal.py")

        with col2:
            with st.container(border=True):
                st.markdown("#### 📥 Citizen Triage")
                st.caption("Review and resolve citizen problem reports assigned to your department.")
                if st.button("Triage Reports", key="auth_btn_triage", use_container_width=True):
                    st.switch_page("pages/5_Authority_Portal.py")

        with col3:
            with st.container(border=True):
                st.markdown("#### 🗺️ City Works Map")
                st.caption("Inspect all active infrastructure corridors across Chennai.")
                if st.button("Explore Map", key="auth_btn_map", use_container_width=True):
                    st.switch_page("pages/1_Explore_Map.py")

        with col4:
            with st.container(border=True):
                st.markdown("#### 🤖 AI Assistant")
                st.caption("Check disruption guidance generated from verified municipal facts.")
                if st.button("Ask Assistant", key="auth_btn_ai", use_container_width=True):
                    st.switch_page("pages/4_AI_Assistant.py")

    elif role == "ADMIN":
        with col1:
            with st.container(border=True):
                st.markdown("#### 🛡️ Admin Portal")
                st.caption("Approve authority officer applications and review audit logs.")
                if st.button("Admin Portal", key="adm_btn_portal", use_container_width=True):
                    st.switch_page("pages/6_Admin_Portal.py")

        with col2:
            with st.container(border=True):
                st.markdown("#### 🏛️ Authority Portal")
                st.caption("Oversee registered public works across municipal departments.")
                if st.button("Authority Portal", key="adm_btn_auth", use_container_width=True):
                    st.switch_page("pages/5_Authority_Portal.py")

        with col3:
            with st.container(border=True):
                st.markdown("#### 🗺️ Corridor Map")
                st.caption("Review spatial corridor map of all city infrastructure projects.")
                if st.button("Explore Map", key="adm_btn_map", use_container_width=True):
                    st.switch_page("pages/1_Explore_Map.py")

        with col4:
            with st.container(border=True):
                st.markdown("#### 🤖 AI Assistant")
                st.caption("Verify the grounded disruption reasoning engine.")
                if st.button("Ask Assistant", key="adm_btn_ai", use_container_width=True):
                    st.switch_page("pages/4_AI_Assistant.py")

else:
    # Unauthenticated View — Dedicated Sign In & Sign Up Portal
    col_info, col_auth = st.columns([1.1, 1.2], gap="large")

    with col_info:
        st.markdown("### Welcome to CivicSync")
        st.markdown("""
        **CivicSync** is a unified civic coordination platform built for Chennai. We bridge the gap between municipal infrastructure execution and citizen mobility.

        - **City-wide Corridor Map:** Real-time visibility into active roadworks, stormwater drains, water pipeline trenching, and metro construction.
        - **Accountable Issue Reporting:** Report potholes, open trenches, and leaks directly to the responsible authority with photo evidence and live status tracking.
        - **Grounded AI Assistant:** Ask questions about timelines and lane barricades with an assistant constrained strictly by verified municipal records.
        - **Authority Governance:** Dedicated triage workspace for municipal engineers to coordinate works and resolve citizen reports.
        """)
        st.info("💡 **Quick Evaluation:** If evaluating the application, switch to the **Demo** tab on the right to sign in instantly with one click.")

    with col_auth:
        st.markdown("### Access CivicSync")
        tab_login, tab_citizen_signup, tab_auth_signup, tab_demo = st.tabs([
            "Sign In",
            "Resident",
            "Authority",
            "Demo"
        ])

        with tab_login:
            st.caption("Sign in with your registered Citizen or Authority credentials.")
            with st.form("login_form"):
                email = st.text_input("Email Address", placeholder="name@domain.com")
                password = st.text_input("Password", type="password")
                submit_login = st.form_submit_button("Sign In", use_container_width=True)

                if submit_login:
                    if not email or not password:
                        st.error("Please enter email and password.")
                    else:
                        with st.spinner("Authenticating with Supabase..."):
                            success, msg, session_data = sign_in_user(email, password)
                            if success and session_data:
                                st.session_state["auth_user"] = session_data
                                st.session_state["auth_profile"] = session_data.get("profile")
                                st.session_state["auth_membership"] = session_data.get("membership")
                                st.session_state["access_token"] = session_data.get("access_token")
                                st.session_state.pop("unverified_email", None)
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                                if "Email not verified" in msg or "not verified" in msg:
                                    st.session_state["unverified_email"] = email.strip()

            if st.session_state.get("unverified_email"):
                u_mail = st.session_state["unverified_email"]
                with st.container(border=True):
                    st.markdown(f"**✉️ Need another verification link?**")
                    st.caption(f"Send a new link to `{u_mail}`:")
                    if st.button("Resend Verification Email", key="resend_mail_btn", use_container_width=True):
                        with st.spinner("Resending verification email..."):
                            res_ok, res_msg = resend_verification_email(u_mail)
                            if res_ok:
                                st.success(res_msg)
                            else:
                                st.error(res_msg)

        with tab_citizen_signup:
            st.caption("Register for public works tracking and filing civic issue reports.")
            with st.form("citizen_signup_form"):
                name = st.text_input("Full Name", placeholder="e.g. Ramesh Kumar")
                su_email = st.text_input("Email", placeholder="ramesh@gmail.com")
                su_pass = st.text_input("Password", type="password")
                su_confirm = st.text_input("Confirm Password", type="password")
                submit_su = st.form_submit_button("Create Citizen Account", use_container_width=True)

                if submit_su:
                    if not name or not su_email or not su_pass:
                        st.error("Please fill in all required fields.")
                    elif su_pass != su_confirm:
                        st.error("Passwords do not match.")
                    else:
                        with st.spinner("Registering citizen account with Supabase Auth..."):
                            ok, reg_msg = sign_up_user(su_email, su_pass, name, role="RESIDENT")
                            if ok:
                                st.success(reg_msg)
                            else:
                                st.error(reg_msg)

        with tab_auth_signup:
            st.caption("Register as an official officer of an approved Chennai civic authority.")
            all_orgs = get_all_organizations()
            org_options = {o["name"]: o["id"] for o in all_orgs}

            with st.form("auth_signup_form"):
                auth_name = st.text_input("Officer Full Name", placeholder="e.g. Er. Sundaram V.")
                auth_email = st.text_input("Official Work Email", placeholder="officer@chennaicorporation.gov.in")
                selected_org_name = st.selectbox(
                    "Select Authority / Department",
                    options=list(org_options.keys()) if org_options else ["Greater Chennai Corporation (Roads Dept)"]
                )
                auth_pass = st.text_input("Password", type="password")
                auth_confirm = st.text_input("Confirm Password", type="password")
                submit_auth = st.form_submit_button("Register as Authority Officer", use_container_width=True)

                if submit_auth:
                    if not auth_name or not auth_email or not auth_pass:
                        st.error("Please fill in all required fields.")
                    elif auth_pass != auth_confirm:
                        st.error("Passwords do not match.")
                    else:
                        chosen_org_id = org_options.get(selected_org_name)
                        with st.spinner("Registering authority officer with Supabase Auth..."):
                            ok, reg_msg = sign_up_user(
                                auth_email,
                                auth_pass,
                                auth_name,
                                role="AUTHORITY",
                                org_id=chosen_org_id,
                                org_name=selected_org_name
                            )
                            if ok:
                                st.success(reg_msg)
                            else:
                                st.error(reg_msg)

        with tab_demo:
            st.markdown("#### Demo Accounts")
            st.caption("Pre-configured accounts for instant evaluation. Click any role to sign in:")

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if st.button("Resident Citizen", use_container_width=True):
                    _switch_demo_account("RESIDENT")
                if st.button("GCC Roads Dept", use_container_width=True):
                    _switch_demo_account("AUTHORITY_GCC")
            with col_d2:
                if st.button("Metro Water (CMWSSB)", use_container_width=True):
                    _switch_demo_account("AUTHORITY_CMWSSB")
                if st.button("Platform Admin", use_container_width=True):
                    _switch_demo_account("ADMIN")

def _switch_demo_account(persona_key: str):
    with st.spinner(f"Authenticating as {persona_key}..."):
        success, msg, session_data = sign_in_demo(persona_key)
        if success and session_data:
            st.session_state["auth_user"] = session_data
            st.session_state["auth_profile"] = session_data.get("profile")
            st.session_state["auth_membership"] = session_data.get("membership")
            st.session_state["access_token"] = session_data.get("access_token")
            st.success(f"Logged in as {persona_key}!")
            st.rerun()
        else:
            st.error(f"Demo sign in error: {msg}")
