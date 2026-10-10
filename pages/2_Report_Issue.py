import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from execution.reports_service import create_citizen_report
from execution.projects_service import get_all_organizations
from ui.nav import render_sidebar
from ui.components import render_header, render_pilot_notice

st.set_page_config(page_title="Report a Problem — CivicSync", page_icon="📢", layout="wide")
render_sidebar()
render_header("Report a Civic Problem", "Submit geo-tagged issues with evidence directly to the responsible Chennai authority")
render_pilot_notice()

user = st.session_state.get("auth_user")
access_token = st.session_state.get("access_token")

if not user:
    st.warning("\u26a0\ufe0f **Sign In Required**: You must be logged in as a resident to submit a civic report. Use the **Demo** tab in the sidebar to sign in instantly.")
    st.stop()

reporter_id = user.get("user_id") if isinstance(user, dict) else user.id

# Fetch Organizations for Routing
orgs = get_all_organizations(access_token=access_token)
org_dict = {o["name"]: o["id"] for o in orgs} if orgs else {}

CATEGORY_MAP = {
    "POTHOLE_ROAD_DAMAGE": "Pothole / Damaged Road Surface",
    "ROAD_OBSTRUCTION": "Road Obstruction / Construction Barrier",
    "BLOCKED_DRAIN": "Blocked Stormwater Drain / Silt Accumulation",
    "WATER_LEAK_PIPE": "Drinking Water Pipeline Leak",
    "SEWERAGE_OVERFLOW": "Sewerage Overflow / Manhole Hazard",
    "STREETLIGHT_POWER": "Streetlight Outage / Hanging Electrical Wire",
    "GARBAGE_WASTE": "Uncollected Solid Waste / Construction Rubble",
    "OTHER": "Other Civic Issue"
}

# Auto-routing recommendation helper
def suggest_org_name(category: str) -> str:
    if category in ["POTHOLE_ROAD_DAMAGE", "ROAD_OBSTRUCTION", "GARBAGE_WASTE", "BLOCKED_DRAIN"]:
        return "Greater Chennai Corporation (Roads Dept)"
    elif category in ["WATER_LEAK_PIPE", "SEWERAGE_OVERFLOW"]:
        return "Chennai Metro Water (CMWSSB)"
    elif category == "STREETLIGHT_POWER":
        return "TANGEDCO / TNPDCL (Chennai Power)"
    return "Greater Chennai Corporation (Roads Dept)"

with st.container():
    st.markdown("### 📝 Issue Submission Form")
    st.caption("Please provide accurate details so the field squad can inspect and resolve the problem.")

    with st.form("citizen_report_form"):
        col1, col2 = st.columns(2)
        with col1:
            selected_cat_key = st.selectbox(
                "Issue Category *",
                options=list(CATEGORY_MAP.keys()),
                format_func=lambda x: CATEGORY_MAP[x]
            )
            title = st.text_input("Summary Title *", placeholder="e.g. Deep pothole causing skidding near bus stop")
            location_desc = st.text_input("Location / Street Landmark *", placeholder="e.g. Anna Salai near Thousand Lights Mosque, opp. bus shelter")

        with col2:
            suggested_org = suggest_org_name(selected_cat_key)
            org_options = list(org_dict.keys())
            default_index = org_options.index(suggested_org) if suggested_org in org_options else 0
            
            chosen_org_name = st.selectbox(
                "Assigned Authority (Auto-Suggested)",
                options=org_options if org_options else ["Greater Chennai Corporation (Roads Dept)"],
                index=default_index if org_options else 0,
                help="We route the report to the responsible authority based on jurisdiction."
            )

            col_lat, col_lon = st.columns(2)
            with col_lat:
                lat = st.number_input("Latitude (Optional)", value=13.0400, format="%.5f")
            with col_lon:
                lon = st.number_input("Longitude (Optional)", value=80.2300, format="%.5f")

        description = st.text_area(
            "Detailed Description *",
            placeholder="Describe the severity, duration of the issue, and any hazards to pedestrians or motorists...",
            height=120
        )

        photo_file = st.file_uploader(
            "📸 Attach Photo Evidence (Optional, max 5MB)",
            type=["jpg", "jpeg", "png", "webp"],
            help="Images are stored in a private secured bucket for verified inspection."
        )

        submit_btn = st.form_submit_button("🚀 Submit Civic Problem Report", use_container_width=True)

        if submit_btn:
            if not title.strip() or not location_desc.strip() or not description.strip():
                st.error("Please fill in the Summary Title, Location, and Description.")
            else:
                photo_bytes = photo_file.read() if photo_file else None
                photo_name = photo_file.name if photo_file else None
                assigned_org_id = org_dict.get(chosen_org_name)

                with st.spinner("Submitting report and uploading evidence..."):
                    success, msg, rep_data = create_citizen_report(
                        reporter_id=reporter_id,
                        category=selected_cat_key,
                        description=description,
                        location_desc=location_desc,
                        latitude=lat,
                        longitude=lon,
                        assigned_org_id=assigned_org_id,
                        photo_bytes=photo_bytes,
                        photo_filename=photo_name,
                        access_token=access_token
                    )

                    if success and rep_data:
                        st.success(f"🎉 {msg}")
                        st.markdown(f"**Report Reference ID:** `{rep_data.get('id')}`")
                        st.info("The assigned civic department has been notified. You can track updates and response notes in **My Reports**.")
                    else:
                        st.error(f"Submission failed: {msg}")

if st.button("👉 Track All My Submitted Reports in 'My Reports'"):
    st.switch_page("pages/3_My_Reports.py")
