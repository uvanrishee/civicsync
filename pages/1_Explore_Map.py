import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from execution.projects_service import get_published_projects, get_project_by_id, get_project_updates
from execution.reports_service import get_all_reports_for_map
from execution.auth_service import save_home_location, reload_profile
from ui.nav import render_sidebar
from ui.map_view import render_interactive_map, render_pin_drop_map
from ui.components import render_header, render_pilot_notice, get_status_badge_html, get_provenance_badge_html

st.set_page_config(page_title="Explore Works Map — CivicSync", page_icon="🗺️", layout="wide")
render_sidebar()
render_header("Explore Chennai Works Map", "Interactive spatial discovery of active infrastructure projects and citizen-reported issues")
render_pilot_notice()

# ------------------------------------------------------------------
# Resident Proximity & Home Location Context
# ------------------------------------------------------------------
user = st.session_state.get("auth_user")
profile = st.session_state.get("auth_profile") or {}
user_role = profile.get("role")
user_id = user.get("user_id") if isinstance(user, dict) else (user.id if user else None)
home_lat = profile.get("home_latitude") if user_role == "RESIDENT" else None
home_lon = profile.get("home_longitude") if user_role == "RESIDENT" else None

if user_role == "RESIDENT":
    if home_lat is not None and home_lon is not None:
        col_banner, col_chg = st.columns([3.5, 1.2], vertical_alignment="center")
        with col_banner:
            st.info(f"📍 **Neighbourhood Active:** Map is centred on your saved area ({home_lat:.4f}, {home_lon:.4f}). Works within **5 km** are marked with red proximity warnings.")
        with col_chg:
            with st.popover("📍 Change Location"):
                st.caption("Click on the map to relocate your neighbourhood centre:")
                temp_chg_lat = st.session_state.get("_chg_home_lat", float(home_lat))
                temp_chg_lon = st.session_state.get("_chg_home_lon", float(home_lon))
                pin_data = render_pin_drop_map(
                    center_lat=temp_chg_lat,
                    center_lon=temp_chg_lon,
                    pinned_lat=temp_chg_lat,
                    pinned_lon=temp_chg_lon,
                    height=280,
                    key="popover_pin_drop"
                )
                clicked = pin_data.get("last_clicked") if pin_data else None
                if clicked and clicked.get("lat") and clicked.get("lng"):
                    clat = round(float(clicked["lat"]), 5)
                    clon = round(float(clicked["lng"]), 5)
                    if clat != temp_chg_lat or clon != temp_chg_lon:
                        st.session_state["_chg_home_lat"] = clat
                        st.session_state["_chg_home_lon"] = clon
                        st.rerun()

                st.write(f"Selected Pin: **{temp_chg_lat:.4f}, {temp_chg_lon:.4f}**")
                if st.button("Save New Location", type="primary", use_container_width=True, key="pop_save_pin"):
                    ok, msg = save_home_location(user_id, temp_chg_lat, temp_chg_lon)
                    if ok:
                        st.session_state["auth_profile"] = reload_profile(user_id)
                        st.session_state.pop("_chg_home_lat", None)
                        st.session_state.pop("_chg_home_lon", None)
                        st.rerun()
                    else:
                        st.error(msg)
    else:
        with st.expander("📍 Set Your Neighbourhood Location (5 km Work Radius)", expanded=False):
            st.caption("Drop a pin to center the map on your neighbourhood and highlight nearby works.")
            temp_set_lat = st.session_state.get("_set_home_lat")
            temp_set_lon = st.session_state.get("_set_home_lon")
            pin_data = render_pin_drop_map(
                center_lat=temp_set_lat if temp_set_lat is not None else 13.0400,
                center_lon=temp_set_lon if temp_set_lon is not None else 80.2300,
                pinned_lat=temp_set_lat,
                pinned_lon=temp_set_lon,
                height=280,
                key="expander_pin_drop"
            )
            clicked = pin_data.get("last_clicked") if pin_data else None
            if clicked and clicked.get("lat") and clicked.get("lng"):
                clat = round(float(clicked["lat"]), 5)
                clon = round(float(clicked["lng"]), 5)
                if clat != temp_set_lat or clon != temp_set_lon:
                    st.session_state["_set_home_lat"] = clat
                    st.session_state["_set_home_lon"] = clon
                    st.rerun()

            if temp_set_lat is not None and temp_set_lon is not None:
                st.write(f"Selected pin: **{temp_set_lat:.4f}, {temp_set_lon:.4f}**")
                if st.button("Save Neighbourhood Location", type="primary", key="exp_save_pin"):
                    ok, msg = save_home_location(user_id, temp_set_lat, temp_set_lon)
                    if ok:
                        st.session_state["auth_profile"] = reload_profile(user_id)
                        st.session_state.pop("_set_home_lat", None)
                        st.session_state.pop("_set_home_lon", None)
                        st.rerun()
                    else:
                        st.error(msg)

# ------------------------------------------------------------------
# Filter Controls
# ------------------------------------------------------------------
with st.container():
    col_cat, col_stat, col_srch, col_rep = st.columns([1.5, 1.2, 2.0, 1.2])
    with col_cat:
        category_choice = st.selectbox(
            "Filter Category",
            ["ALL", "ROADWORKS", "DRAINAGE", "WATER_SEWERAGE", "ELECTRICAL", "METRO_RAIL", "OTHER"],
            index=0
        )
    with col_stat:
        status_choice = st.selectbox(
            "Status",
            ["ALL", "IN_PROGRESS", "PLANNED", "COMPLETED", "DELAYED"],
            index=0
        )
    with col_srch:
        search_query = st.text_input("Search Location or Title", placeholder="e.g. Anna Salai, Guindy, T. Nagar")
    with col_rep:
        toggle_reports = st.checkbox("Show Citizen Issues", value=True)

# ------------------------------------------------------------------
# Fetch Data
# ------------------------------------------------------------------
access_token = st.session_state.get("access_token")
projects = get_published_projects(access_token=access_token, category=category_choice, status=status_choice, search=search_query)

# Always fetch all geo-tagged reports for the map (service role, public read)
all_reports = get_all_reports_for_map() if toggle_reports else []

# ------------------------------------------------------------------
# Map Legend
# ------------------------------------------------------------------
st.markdown("""
<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 14px; margin: 4px 0 12px 0; display: flex; flex-direction: column; gap: 6px; font-size: 12px;">
    <div style="display: flex; gap: 16px; flex-wrap: wrap; align-items: center;">
        <span style="font-weight: 600; color: #1E293B;">Layer Types:</span>
        <span style="display: inline-flex; align-items: center; gap: 6px; color: #0F766E;">
            <span style="width: 10px; height: 10px; border-radius: 50%; background: #0F766E; display: inline-block;"></span> <strong>Public Works</strong> (Active Projects)
        </span>
        <span style="display: inline-flex; align-items: center; gap: 6px; color: #475569;">
            <span style="width: 10px; height: 10px; border-radius: 50%; background: #EF4444; display: inline-block;"></span> <strong>Citizen Reports</strong> (Civic Issues)
        </span>
        <span style="display: inline-flex; align-items: center; gap: 6px; color: #DC2626;">
            <span style="width: 12px; height: 12px; border-radius: 50%; background: rgba(220, 38, 38, 0.25); border: 1px solid #DC2626; display: inline-block;"></span> 5 km Warning Overlay
        </span>
    </div>
    <div style="display: flex; gap: 14px; flex-wrap: wrap; align-items: center; border-top: 1px dashed #E2E8F0; padding-top: 6px;">
        <span style="font-weight: 600; color: #1E293B;">Citizen Report Status:</span>
        <span style="display: inline-flex; align-items: center; gap: 4px; color: #B91C1C;">
            <span style="width: 8px; height: 8px; border-radius: 50%; background: #EF4444; display: inline-block;"></span> Pending
        </span>
        <span style="display: inline-flex; align-items: center; gap: 4px; color: #C2410C;">
            <span style="width: 8px; height: 8px; border-radius: 50%; background: #F97316; display: inline-block;"></span> Acknowledged
        </span>
        <span style="display: inline-flex; align-items: center; gap: 4px; color: #1D4ED8;">
            <span style="width: 8px; height: 8px; border-radius: 50%; background: #3B82F6; display: inline-block;"></span> In Progress
        </span>
        <span style="display: inline-flex; align-items: center; gap: 4px; color: #15803D;">
            <span style="width: 8px; height: 8px; border-radius: 50%; background: #22C55E; display: inline-block;"></span> Resolved
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Map + Detail Panel
# ------------------------------------------------------------------
col_map, col_details = st.columns([1.8, 1.2])

with col_map:
    st.markdown("#### Interactive Chennai Corridor Map")
    map_data = render_interactive_map(
        projects,
        reports=all_reports,
        show_reports=toggle_reports,
        home_lat=home_lat,
        home_lon=home_lon,
    )

    # Detect clicks — match against project IDs first, then report IDs
    if map_data and map_data.get("last_object_clicked_popup"):
        popup_text = str(map_data["last_object_clicked_popup"])

        # Reset selection flags
        clicked_project = None
        clicked_report  = None

        for p in projects:
            if p.get("id") and p["id"][:8] in popup_text:
                clicked_project = p["id"]
                break

        if not clicked_project:
            for r in all_reports:
                if r.get("id") and r["id"][:8] in popup_text:
                    clicked_report = r["id"]
                    break

        if clicked_project:
            st.session_state["selected_project_id"] = clicked_project
            st.session_state.pop("selected_report_id", None)
        elif clicked_report:
            st.session_state["selected_report_id"] = clicked_report
            st.session_state.pop("selected_project_id", None)

# ------------------------------------------------------------------
# Right Panel: Project OR Report detail
# ------------------------------------------------------------------
with col_details:
    selected_project_id = st.session_state.get("selected_project_id")
    selected_report_id  = st.session_state.get("selected_report_id")

    # Default: show first project if nothing selected yet
    if not selected_project_id and not selected_report_id and projects:
        selected_project_id = projects[0].get("id")

    # ---- PROJECT DETAIL ----
    if selected_project_id and not selected_report_id:
        st.markdown("#### 🏗️ Project Dossier")
        proj = get_project_by_id(selected_project_id, access_token=access_token)
        if proj:
            p_title      = proj.get("title")
            p_cat        = proj.get("category")
            p_org        = proj.get("organizations", {}).get("name") if isinstance(proj.get("organizations"), dict) else "Public Authority"
            p_status     = proj.get("status")
            p_origin     = proj.get("data_origin")
            p_loc        = proj.get("location_name")
            p_stretch    = proj.get("road_stretch_desc") or "Corridor bounds not specified"
            p_start      = proj.get("planned_start_date")
            p_end        = proj.get("current_estimated_end_date")
            p_disruption = proj.get("expected_disruption") or "No special disruption recorded."

            st.markdown(f"""
            <div class="civic-card">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <div>{get_provenance_badge_html(p_origin)}</div>
                    <div>{get_status_badge_html(p_status)}</div>
                </div>
                <h3 style="margin: 4px 0 6px 0; color: #172B4D;">{p_title}</h3>
                <p style="margin: 0 0 6px 0; color: #64748B;"><strong>Managing Body:</strong> {p_org}</p>
                <p style="margin: 0 0 6px 0; color: #1E293B;"><strong>Corridor:</strong> {p_loc} ({p_stretch})</p>
                <div style="background: #F8FAFC; padding: 8px 12px; border-radius: 6px; border: 1px solid #E2E8F0; margin: 8px 0;">
                    <div>📅 <strong>Schedule:</strong> {p_start} → <strong>{p_end}</strong></div>
                    <div style="margin-top: 4px; color: #DC2626;">⚠️ <strong>Advisory:</strong> {p_disruption}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            updates = get_project_updates(selected_project_id, access_token=access_token)
            st.markdown("##### Official Progress Timeline")
            if updates:
                for u in updates:
                    u_date = str(u.get("created_at"))[:10]
                    u_note = u.get("update_note")
                    u_stat = u.get("status_at_update")
                    st.markdown(f"- **{u_date}** [{u_stat}]: {u_note}")
            else:
                st.caption("No progress updates logged yet.")

            st.divider()
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Ask AI Assistant", use_container_width=True):
                    st.session_state["selected_project_id"] = selected_project_id
                    st.switch_page("pages/4_AI_Assistant.py")
            with col_b:
                if st.button("Report Issue Here", use_container_width=True):
                    st.switch_page("pages/2_Report_Issue.py")
        else:
            st.info("Selected project could not be found.")

    # ---- REPORT DETAIL ----
    elif selected_report_id:
        st.markdown("#### ⚠️ Citizen Report Detail")
        rep = next((r for r in all_reports if r.get("id") == selected_report_id), None)

        if rep:
            STATUS_BADGE = {
                "PENDING_REVIEW":  ("#FEF3C7", "#B45309", "⏳ Pending Review"),
                "ACKNOWLEDGED":    ("#FEF3C7", "#D97706", "👁️ Acknowledged"),
                "IN_PROGRESS":     ("#DBEAFE", "#1D4ED8", "🔧 In Progress"),
                "RESOLVED":        ("#DCFCE7", "#15803D", "✅ Resolved"),
                "REJECTED":        ("#FEE2E2", "#B91C1C", "❌ Rejected"),
                "REDIRECTED":      ("#F3F4F6", "#374151", "↩️ Redirected"),
            }
            r_cat    = rep.get("category", "OTHER").replace("_", " ").title()
            r_status = rep.get("status", "PENDING_REVIEW")
            r_loc    = rep.get("location_desc") or "Location not specified"
            r_desc   = rep.get("description") or "No description provided."
            r_date   = str(rep.get("created_at", ""))[:10]
            r_id     = rep.get("id", "")
            org_obj  = rep.get("organizations")
            r_org    = org_obj.get("name") if isinstance(org_obj, dict) else "Public Authority"

            badge_bg, badge_fg, badge_label = STATUS_BADGE.get(r_status, ("#F3F4F6", "#374151", r_status))

            st.markdown(f"""
            <div class="civic-card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 10px;">
                    <span style="font-size:11px; font-weight:700; color:#D97706; letter-spacing:0.5px;">⚠️ CITIZEN ISSUE REPORT</span>
                    <span style="background:{badge_bg}; color:{badge_fg}; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600;">{badge_label}</span>
                </div>
                <h3 style="margin: 0 0 8px 0; color:#172B4D;">{r_cat}</h3>
                <div style="font-size:13px; color:#475569; margin-bottom:6px;">📍 <strong>Location:</strong> {r_loc}</div>
                <div style="background:#F8FAFC; padding:10px 12px; border-radius:8px; border:1px solid #E2E8F0; margin-bottom:10px; font-size:13px; color:#334155; line-height:1.6;">
                    {r_desc}
                </div>
                <div style="font-size:12px; color:#64748B; margin-bottom:4px;">🏛️ <strong>Assigned To:</strong> {r_org}</div>
                <div style="font-size:11px; color:#94A3B8;">📅 Filed: {r_date} &nbsp;|&nbsp; Ref: <code>{r_id[:8]}…</code></div>
            </div>
            """, unsafe_allow_html=True)

            col_x, col_y = st.columns(2)
            with col_x:
                if st.button("🗺️ View All Reports", use_container_width=True):
                    st.session_state.pop("selected_report_id", None)
                    st.rerun()
            with col_y:
                if st.button("📢 File a New Report", use_container_width=True):
                    st.switch_page("pages/2_Report_Issue.py")
        else:
            st.info("Report details not found.")

    else:
        st.info("Click any marker on the map to view details here.")

# ------------------------------------------------------------------
# Summary Stats Row
# ------------------------------------------------------------------
st.divider()
stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
with stat_col1:
    st.metric("Active Projects", len([p for p in projects if p.get("status") == "IN_PROGRESS"]))
with stat_col2:
    st.metric("Total Reports", len(all_reports))
with stat_col3:
    pending = len([r for r in all_reports if r.get("status") == "PENDING_REVIEW"])
    st.metric("Pending Review", pending)
with stat_col4:
    resolved = len([r for r in all_reports if r.get("status") == "RESOLVED"])
    st.metric("Resolved", resolved)

# Project Table at Bottom
st.markdown("#### All Matching Projects")
if projects:
    table_data = []
    for p in projects:
        raw_status = p.get("status") or "UNKNOWN"
        formatted_status = raw_status.replace("_", " ").title()
        raw_category = p.get("category") or "OTHER"
        formatted_category = raw_category.replace("_", " ").title()

        table_data.append({
            "Title": p.get("title"),
            "Sector": formatted_category,
            "Location": p.get("location_name"),
            "Status": formatted_status,
            "Target Completion": p.get("current_estimated_end_date"),
            "Authority": p.get("organizations", {}).get("name") if isinstance(p.get("organizations"), dict) else "Public Authority"
        })
    st.dataframe(table_data, use_container_width=True, hide_index=True)
