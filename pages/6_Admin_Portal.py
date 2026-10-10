import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from execution.env_config import ADMIN_ACCESS_KEY
from execution.supabase_client import get_authenticated_client, get_service_role_client
from ui.nav import render_sidebar
from ui.components import render_header, render_pilot_notice

st.set_page_config(page_title="Platform Admin Portal — CivicSync", page_icon="🛡️", layout="wide")
render_sidebar()
render_header("Platform Administration Portal", "Governance oversight, organization membership approvals, and system audit log")
render_pilot_notice()

user = st.session_state.get("auth_user")
profile = st.session_state.get("auth_profile")
access_token = st.session_state.get("access_token")

# Enforce Role Check
user_role = profile.get("role") if profile else None
if user_role != "ADMIN":
    st.error("⛔ **Restricted Area**: This portal is reserved for Platform Administrators.")
    st.info("💡 Switch to the **Platform Admin** demo account in the sidebar to review governance capabilities.")
    st.stop()

# Admin Passcode Barrier
st.markdown("### 🔐 Administrative Verification Passcode")
admin_passcode = st.text_input(
    "Enter Admin Access Key",
    type="password",
    help="Loaded from ADMIN_ACCESS_KEY in .env to prevent unauthorized demo tamper."
)

if admin_passcode != ADMIN_ACCESS_KEY:
    st.warning("⚠️ Please provide the configured `ADMIN_ACCESS_KEY` to unlock administrative actions.")
    st.caption("*(Default local key for hackathon evaluation: `civicsync-admin-secret-2026`)*")
    st.stop()

st.success("🔓 Administrative clearance verified.")

tab_approvals, tab_audit = st.tabs(["🏛️ Organization Approvals", "📜 Platform Audit Log"])

# After role check and passcode verification, engage admin database client
client = get_service_role_client() or get_authenticated_client(access_token)
user_id = user.get("user_id") if isinstance(user, dict) else user.id

with tab_approvals:
    st.markdown("#### Pending Authority Membership Applications")
    if not client:
        st.error("Database client is not available.")
    else:
        try:
            pending_res = client.table("organization_memberships").select("*, organizations(name)").eq("status", "PENDING").execute()
            pending_list = pending_res.data or []

            # Retrieve profile display names for pending applicants
            applicant_names = {}
            if pending_list:
                u_ids = [m.get("user_id") for m in pending_list if m.get("user_id")]
                if u_ids:
                    try:
                        p_res = client.table("profiles").select("id, display_name").in_("id", u_ids).execute()
                        applicant_names = {p["id"]: p.get("display_name") for p in (p_res.data or [])}
                    except Exception:
                        pass

            if not pending_list:
                st.info("No pending authority membership applications at this time.")
            else:
                for app in pending_list:
                    m_id = app.get("id")
                    uid = app.get("user_id")
                    applicant_name = applicant_names.get(uid, "Officer Applicant")
                    target_org = app.get("organizations", {}).get("name", "Unknown Organization")
                    role_in_org = app.get("role_in_org", "OFFICER")

                    with st.container():
                        st.markdown(f"""
                        <div class="civic-card">
                            <strong>Applicant:</strong> {applicant_name} <br>
                            <strong>Target Organization:</strong> {target_org} ({role_in_org})
                        </div>
                        """, unsafe_allow_html=True)

                        col_app, col_rej = st.columns([1, 1])
                        with col_app:
                            if st.button(f"Approve {applicant_name}", key=f"app_{m_id}"):
                                client.table("organization_memberships").update({"status": "APPROVED", "approved_by": user_id}).eq("id", m_id).execute()
                                # Audit log
                                client.table("audit_logs").insert({
                                    "actor_id": user_id,
                                    "action_type": "MEMBERSHIP_APPROVED",
                                    "entity_type": "ORGANIZATION_MEMBERSHIP",
                                    "entity_id": m_id,
                                    "summary": f"Approved membership for {applicant_name} in {target_org}"
                                }).execute()
                                st.success("Membership approved!")
                                st.rerun()

                        with col_rej:
                            if st.button(f"Reject {applicant_name}", key=f"rej_{m_id}"):
                                client.table("organization_memberships").update({"status": "REJECTED"}).eq("id", m_id).execute()
                                client.table("audit_logs").insert({
                                    "actor_id": user_id,
                                    "action_type": "MEMBERSHIP_REJECTED",
                                    "entity_type": "ORGANIZATION_MEMBERSHIP",
                                    "entity_id": m_id,
                                    "summary": f"Rejected membership for {applicant_name} in {target_org}"
                                }).execute()
                                st.warning("Membership rejected.")
                                st.rerun()
        except Exception as e:
            st.error(f"Error fetching pending memberships: {e}")

with tab_audit:
    st.markdown("#### System Activity & Governance Audit Log")
    if client:
        try:
            audit_res = client.table("audit_logs").select("*").order("created_at", desc=True).limit(50).execute()
            logs = audit_res.data or []
            if logs:
                st.dataframe(logs, use_container_width=True)
            else:
                st.caption("No administrative audit entries logged yet.")
        except Exception as e:
            st.error(f"Error fetching audit log: {e}")
