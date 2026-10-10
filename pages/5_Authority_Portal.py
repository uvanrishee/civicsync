import streamlit as st
import sys
from pathlib import Path
from datetime import date, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from execution.projects_service import create_project, add_project_update, get_organization_projects
from execution.reports_service import get_assigned_organization_reports, update_report_status, get_signed_evidence_url
from ui.nav import render_sidebar
from ui.components import render_header, render_pilot_notice, get_status_badge_html, get_provenance_badge_html

st.set_page_config(page_title="Authority Portal — CivicSync", page_icon="🏛️", layout="wide")
render_sidebar()
render_header("Authority Work & Triage Portal", "Register infrastructure projects, publish timeline updates, and resolve citizen reports")
render_pilot_notice()

user = st.session_state.get("auth_user")
profile = st.session_state.get("auth_profile")
membership = st.session_state.get("auth_membership")
access_token = st.session_state.get("access_token")

# Enforce Role Check
user_role = profile.get("role") if profile else None
if user_role not in ["AUTHORITY", "ADMIN"]:
    st.error("⛔ **Access Restricted**: You must belong to an approved civic organization to access the Authority Portal. Switch to the **GCC Roads Dept** or **Metro Water** demo in the sidebar to test authority operations.")
    st.stop()

# Identify Organization Context
org_id = membership.get("organization_id") if membership else None
org_name = membership.get("organizations", {}).get("name") if membership else "Public Authority"
user_id = user.get("user_id") if isinstance(user, dict) else user.id

# Fallback if admin without explicit org membership
if not org_id:
    # Pick first org for admin testing
    from execution.projects_service import get_all_organizations
    all_orgs = get_all_organizations(access_token)
    if all_orgs:
        org_id = all_orgs[0]["id"]
        org_name = all_orgs[0]["name"]

st.markdown(f"**Managing for Organization:** `{org_name}`")

tab_reg, tab_my_proj, tab_triage = st.tabs([
    "➕ Register Public Work",
    "📊 Update Project Progress",
    "📥 Citizen Reports Inbox"
])

# -------------------------------------------------------------
# TAB 1: REGISTER PUBLIC WORK
# -------------------------------------------------------------
with tab_reg:
    st.markdown("#### Register New Public Work")
    st.caption("Publish work timelines and disruption advisories to the public Chennai map.")

    with st.form("register_work_form"):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Project Title *", placeholder="e.g. Stormwater Drain Culvert Reconstruction")
            category = st.selectbox(
                "Sector Category *",
                ["ROADWORKS", "DRAINAGE", "WATER_SEWERAGE", "ELECTRICAL", "METRO_RAIL", "OTHER"]
            )
            location_name = st.text_input("Corridor Landmark / Area *", placeholder="e.g. Anna Salai, Guindy")
            road_stretch = st.text_input("Affected Road Stretch Description", placeholder="e.g. Between Kathipara and Nandanam")

        with col2:
            road_segment_id = st.text_input("Canonical Corridor Segment ID (Optional)", placeholder="e.g. CHN-CORR-ANNASALAI-01")
            col_l1, col_l2 = st.columns(2)
            with col_l1:
                lat = st.number_input("Latitude (WGS84)", value=13.0100, format="%.5f")
            with col_l2:
                lon = st.number_input("Longitude (WGS84)", value=80.2150, format="%.5f")

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                start_date = st.date_input("Planned Start Date", value=date.today())
            with col_d2:
                end_date = st.date_input("Target Completion Date", value=date.today() + timedelta(days=45))

        description = st.text_area(
            "Project Scope & Description *",
            placeholder="Detailed description of the civic objective, contractors, and construction phases...",
            height=100
        )

        expected_disruption = st.text_area(
            "Expected Traffic & Pedestrian Disruption *",
            placeholder="Specify lane closures, working hours, diversions, or expected congestion windows...",
            height=80
        )

        submit_work = st.form_submit_button("🚀 Publish Project to Public Registry", use_container_width=True)

        if submit_work:
            if not title.strip() or not description.strip() or not location_name.strip() or not expected_disruption.strip():
                st.error("Please fill in all required fields marked with *.")
            else:
                # Automatic Demo Provenance Guardrail:
                is_demo_user = "demo" in str(user.get("email", "")).lower()
                origin = "DEMO_DATA" if is_demo_user else "ORGANIZATION_ENTERED"

                payload = {
                    "organization_id": org_id,
                    "created_by": user_id,
                    "title": title.strip(),
                    "description": description.strip(),
                    "category": category,
                    "location_name": location_name.strip(),
                    "road_stretch_desc": road_stretch.strip() if road_stretch else None,
                    "road_segment_id": road_segment_id.strip() if road_segment_id else None,
                    "latitude": lat,
                    "longitude": lon,
                    "planned_start_date": str(start_date),
                    "original_estimated_end_date": str(end_date),
                    "current_estimated_end_date": str(end_date),
                    "status": "IN_PROGRESS",
                    "expected_disruption": expected_disruption.strip(),
                    "publication_status": "PUBLISHED",
                    "data_origin": origin
                }

                with st.spinner("Persisting project in Supabase..."):
                    ok, msg, created_proj = create_project(payload, access_token=access_token)
                    if ok:
                        st.success(f"🎉 {msg} (Tagged: {origin})")
                        st.info("The project is now live on the Chennai interactive map!")
                    else:
                        st.error(f"Error registering project: {msg}")

# -------------------------------------------------------------
# TAB 2: UPDATE PROJECT PROGRESS
# -------------------------------------------------------------
with tab_my_proj:
    st.markdown("#### Manage Ongoing Projects & Log Timeline Updates")
    org_projects = get_organization_projects(org_id, access_token=access_token)

    if not org_projects:
        st.info("No projects registered for this organization yet.")
    else:
        proj_select_map = {f"{p.get('title')} ({p.get('location_name')})": p.get("id") for p in org_projects}
        chosen_p_name = st.selectbox("Select Project to Update", list(proj_select_map.keys()))
        target_p_id = proj_select_map[chosen_p_name]

        # Display current info
        curr_p = next((p for p in org_projects if p.get("id") == target_p_id), None)
        if curr_p:
            st.markdown(f"**Current Status:** `{curr_p.get('status')}` | **Target Completion:** `{curr_p.get('current_estimated_end_date')}`")

        with st.form("add_update_form"):
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                new_status = st.selectbox("Updated Status", ["IN_PROGRESS", "DELAYED", "COMPLETED", "CANCELLED"])
            with col_u2:
                revised_end = st.date_input("Revised Completion Date (Optional)", value=None)

            update_note = st.text_area("Progress Note / Milestone *", placeholder="e.g. Concrete curing completed. Asphalt topcoat commencing tonight.")
            reason = st.text_input("Reason for Schedule Adjustment (if applicable)", placeholder="e.g. Unforeseen monsoon rains and utility relocation")

            submit_update = st.form_submit_button("📝 Append Progress Update to Timeline", use_container_width=True)

            if submit_update:
                if not update_note.strip():
                    st.error("Please provide an update note.")
                else:
                    with st.spinner("Recording progress update..."):
                        ok, msg = add_project_update(
                            project_id=target_p_id,
                            author_id=user_id,
                            status_at_update=new_status,
                            update_note=update_note,
                            revised_estimated_end_date=str(revised_end) if revised_end else None,
                            reason_for_change=reason if reason else None,
                            access_token=access_token
                        )
                        if ok:
                            st.success(f"🎉 {msg}")
                            st.rerun()
                        else:
                            st.error(f"Error: {msg}")

# -------------------------------------------------------------
# TAB 3: CITIZEN REPORTS TRIAGE INBOX
# -------------------------------------------------------------
with tab_triage:
    st.markdown("#### Citizen Reports Triage Inbox")
    st.caption("Reports assigned to your organization by citizens. Review, acknowledge, and resolve.")

    assigned_reports = get_assigned_organization_reports(org_id, access_token=access_token)

    if not assigned_reports:
        st.info("No citizen reports currently assigned to this organization.")
    else:
        st.markdown(f"Found **{len(assigned_reports)}** assigned reports.")

        status_icons = {
            "PENDING_REVIEW": "⏳ Pending",
            "ACKNOWLEDGED": "🟠 Acknowledged",
            "IN_PROGRESS": "🔵 In Progress",
            "RESOLVED": "🟢 Resolved",
            "REDIRECTED": "↩️ Redirected",
            "REJECTED": "❌ Rejected"
        }

        for rep in assigned_reports:
            r_id = rep.get("id")
            r_title = rep.get("title") or rep.get("category", "Civic Issue")
            r_cat = rep.get("category")
            r_loc = rep.get("location_desc")
            r_status = rep.get("status")
            r_desc = rep.get("description")
            r_photo = rep.get("photo_storage_path")

            status_label = status_icons.get(r_status, r_status)
            clean_cat = r_cat.replace("_", " ").title() if r_cat else "Civic Issue"

            with st.expander(f"{status_label} · {clean_cat} — {r_loc}", expanded=False):
                st.markdown(f"""
                <div style="background: #F8FAFC; padding: 10px 14px; border-radius: 6px; border: 1px solid #E2E8F0; margin-bottom: 10px; font-size: 0.9rem;">
                    <div><strong>Category:</strong> {clean_cat} &nbsp;|&nbsp; <strong>Ref ID:</strong> <code>{r_id[:8]}...</code></div>
                    <div style="margin-top: 4px;"><strong>Location:</strong> {r_loc}</div>
                    <div style="margin-top: 6px; padding-top: 6px; border-top: 1px dashed #E2E8F0;"><strong>Citizen Description:</strong> {r_desc}</div>
                </div>
                """, unsafe_allow_html=True)

                if r_photo:
                    signed_img = get_signed_evidence_url(r_photo, access_token=access_token)
                    if signed_img:
                        st.image(signed_img, caption="Citizen Photo Evidence", width=300)

                # Action Form
                with st.form(f"triage_form_{r_id}"):
                    col_t1, col_t2 = st.columns(2)
                    with col_t1:
                        target_status = st.selectbox(
                            "Transition Status",
                            ["ACKNOWLEDGED", "IN_PROGRESS", "RESOLVED", "REDIRECTED", "REJECTED"],
                            index=0 if r_status == "PENDING_REVIEW" else (1 if r_status == "ACKNOWLEDGED" else 2)
                        )
                    with col_t2:
                        res_summary = st.text_input("Resolution Summary (Required if RESOLVED)", placeholder="e.g. Cold-mix patching completed by Zone 9 road squad.")

                    officer_note = st.text_input("Internal / Audit Note *", placeholder="e.g. Field squad dispatched for inspection.")
                    btn_triage = st.form_submit_button("Update Report Workflow Status")

                    if btn_triage:
                        if not officer_note.strip():
                            st.error("Please enter an officer note.")
                        elif target_status == "RESOLVED" and not res_summary.strip():
                            st.error("Resolution summary is required when marking a report as RESOLVED.")
                        else:
                            with st.spinner("Updating report status in database..."):
                                ok, t_msg = update_report_status(
                                    report_id=r_id,
                                    new_status=target_status,
                                    actor_id=user_id,
                                    note=officer_note,
                                    resolution_summary=res_summary if target_status == "RESOLVED" else None,
                                    access_token=access_token
                                )
                                if ok:
                                    st.success(t_msg)
                                    st.rerun()
                                else:
                                    st.error(t_msg)
