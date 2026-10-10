import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from execution.reports_service import get_resident_reports, get_report_history, get_signed_evidence_url
from ui.nav import render_sidebar
from ui.components import render_header, render_pilot_notice, get_status_badge_html

st.set_page_config(page_title="My Reports — CivicSync", page_icon="📋", layout="wide")
render_sidebar()
render_header("My Civic Reports", "Track the status, authority response notes, and resolution history of your filed issues")
render_pilot_notice()

user = st.session_state.get("auth_user")
access_token = st.session_state.get("access_token")

if not user:
    st.warning("⚠️ **Sign In Required**: Please log in as a resident to view your reported issues. Use the **Demo** tab in the sidebar to sign in instantly.")
    st.stop()

reporter_id = user.get("user_id") if isinstance(user, dict) else user.id

reports = get_resident_reports(reporter_id, access_token=access_token)

if not reports:
    st.info("You haven't submitted any civic issue reports yet.")
    if st.button("📢 File a New Problem Report Now"):
        st.switch_page("pages/2_Report_Issue.py")
else:
    st.markdown(f"### 📋 Your Filed Reports ({len(reports)})")
    
    for rep in reports:
        rep_id = rep.get("id")
        title = rep.get("title") or rep.get("category", "Civic Problem")
        cat = rep.get("category")
        loc = rep.get("location_desc")
        status = rep.get("status")
        created_at = str(rep.get("created_at"))[:16]
        org_name = rep.get("organizations", {}).get("name") if isinstance(rep.get("organizations"), dict) else "Assigned Department"
        photo_path = rep.get("photo_storage_path")
        resolution = rep.get("resolution_summary")

        with st.container():
            st.markdown(f"""
            <div class="civic-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-size: 0.8rem; color: #64748B;">Ref ID: <code>{rep_id[:8]}...</code> | Filed on: {created_at}</span>
                    <div>{get_status_badge_html(status)}</div>
                </div>
                <h4 style="margin: 4px 0 6px 0; color: #172B4D;">{title}</h4>
                <p style="margin: 0 0 6px 0; font-size: 0.9rem; color: #334155;">📍 <strong>Location:</strong> {loc}</p>
                <p style="margin: 0 0 6px 0; font-size: 0.9rem; color: #475569;">🏛️ <strong>Assigned Authority:</strong> {org_name}</p>
                <p style="margin: 6px 0; font-size: 0.88rem; color: #1E293B; background: #F8FAFC; padding: 8px; border-radius: 6px; border: 1px solid #E2E8F0;">
                    {rep.get('description')}
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Columns for Evidence Photo and Progress History
            col_photo, col_hist = st.columns([1.0, 1.5])

            with col_photo:
                if photo_path:
                    signed_url = get_signed_evidence_url(photo_path, access_token=access_token)
                    if signed_url:
                        st.image(signed_url, caption="Attached Evidence Photo", use_container_width=True)
                    else:
                        st.caption("📷 Photo attached (secure private preview)")
                else:
                    st.caption("No photo evidence attached.")

            with col_hist:
                if resolution:
                    st.success(f"✅ **Resolution Note:** {resolution}")

                history = get_report_history(rep_id, access_token=access_token)
                st.markdown("##### 📜 Activity & Status History")
                if history:
                    for h in history:
                        h_time = str(h.get("created_at"))[:16]
                        h_new = h.get("new_status")
                        h_note = h.get("note") or "Status changed"
                        st.markdown(f"- **{h_time}** → `{h_new}`: {h_note}")
                else:
                    st.caption("Awaiting initial authority triage.")

            st.divider()
