import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from execution.supabase_client import get_authenticated_client, get_anon_client, get_service_role_client

logger = logging.getLogger(__name__)

STORAGE_BUCKET = "civicsync-evidence"

def create_citizen_report(
    reporter_id: str,
    category: str,
    description: str,
    location_desc: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    assigned_org_id: Optional[str] = None,
    photo_bytes: Optional[bytes] = None,
    photo_filename: Optional[str] = None,
    access_token: Optional[str] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Submits a new citizen problem report, optionally uploading a photo to private Storage.
    """
    client = get_authenticated_client(access_token)
    if not client:
        return False, "Database client is not available.", None

    if not description.strip() or not location_desc.strip():
        return False, "Description and Location are required.", None

    report_id = str(uuid.uuid4())
    photo_storage_path = None

    # Handle photo upload if present
    if photo_bytes and photo_filename:
        # Uniform storage path: reports/{user_id}/{report_id}/{filename}
        clean_filename = photo_filename.replace(" ", "_")
        storage_path = f"reports/{reporter_id}/{report_id}/{clean_filename}"
        try:
            client.storage.from_(STORAGE_BUCKET).upload(
                path=storage_path,
                file=photo_bytes,
                file_options={"content-type": "image/jpeg", "upsert": "true"}
            )
            photo_storage_path = storage_path
        except Exception as e:
            logger.warning(f"Could not upload evidence image: {e}. Proceeding with report submission.")

    report_payload = {
        "id": report_id,
        "reporter_id": reporter_id,
        "category": category,
        "description": description.strip(),
        "location_desc": location_desc.strip(),
        "latitude": latitude,
        "longitude": longitude,
        "photo_storage_path": photo_storage_path,
        "assigned_organization_id": assigned_org_id,
        "status": "PENDING_REVIEW"
    }

    try:
        res = client.table("reports").insert(report_payload).execute()
        if not res.data:
            return False, "Failed to persist report in database.", None

        # Add initial audit update
        update_payload = {
            "report_id": report_id,
            "actor_id": reporter_id,
            "previous_status": "NONE",
            "new_status": "PENDING_REVIEW",
            "note": "Citizen submitted issue report."
        }
        client.table("report_updates").insert(update_payload).execute()

        return True, "Problem report submitted successfully!", res.data[0]

    except Exception as e:
        logger.error(f"Error submitting citizen report: {e}")
        return False, f"Database error submitting report: {e}", None

def get_resident_reports(reporter_id: str, access_token: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves all reports filed by the signed-in resident."""
    client = get_authenticated_client(access_token)
    if not client:
        return []

    try:
        res = client.table("reports").select("*, organizations(name, org_type)").eq("reporter_id", reporter_id).order("created_at", desc=True).execute()
        return res.data or []
    except Exception as e:
        logger.error(f"Error fetching resident reports: {e}")
        return []

def get_assigned_organization_reports(organization_id: str, access_token: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves reports assigned to an organization's triage inbox.
    Uses service role client to bypass RLS — authorities need to read
    citizen reports (not their own rows), so the standard auth policy
    would block this query.
    """
    client = get_service_role_client()
    if not client:
        return []

    try:
        res = (
            client.table("reports")
            .select("*")
            .eq("assigned_organization_id", organization_id)
            .order("created_at", desc=True)
            .execute()
        )
        return res.data or []
    except Exception as e:
        logger.error(f"Error fetching org reports: {e}")
        return []

def get_report_history(report_id: str, access_token: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves chronological activity updates for a report."""
    # Use service role to bypass RLS — both citizens and authorities
    # need to read audit trail, but they don't own the rows.
    client = get_service_role_client()
    if not client:
        return []

    try:
        res = client.table("report_updates").select("*").eq("report_id", report_id).order("created_at", desc=False).execute()
        return res.data or []
    except Exception as e:
        logger.error(f"Error fetching report updates: {e}")
        return []

def update_report_status(
    report_id: str,
    new_status: str,
    actor_id: str,
    note: str,
    resolution_summary: Optional[str] = None,
    access_token: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Updates a report's status and adds an audit record.
    Uses service role client to bypass RLS — authorities updating
    citizen-owned report rows would otherwise be blocked.
    """
    client = get_service_role_client()
    if not client:
        return False, "Database client is not available."

    try:
        # Get current status
        curr = client.table("reports").select("status").eq("id", report_id).single().execute()
        prev_status = curr.data.get("status") if curr.data else "UNKNOWN"

        update_payload: Dict[str, Any] = {
            "status": new_status,
            "updated_at": "now()"
        }
        if resolution_summary:
            update_payload["resolution_summary"] = resolution_summary.strip()

        client.table("reports").update(update_payload).eq("id", report_id).execute()

        # Insert audit history
        client.table("report_updates").insert({
            "report_id": report_id,
            "actor_id": actor_id,
            "previous_status": prev_status,
            "new_status": new_status,
            "note": note.strip()
        }).execute()

        return True, f"Report status successfully updated to {new_status}."
    except Exception as e:
        logger.error(f"Error updating report status: {e}")
        return False, f"Failed to update report status: {e}"

def get_all_reports_for_map() -> List[Dict[str, Any]]:
    """
    Fetches all citizen reports that have geo-coordinates, for display on the public map.
    Uses service role so anyone (including unauthenticated visitors) can see the live issue heatmap.
    Only returns reports with valid lat/lon so the map isn't cluttered.
    """
    client = get_service_role_client()
    if not client:
        return []
    try:
        res = (
            client.table("reports")
            .select("id, category, description, location_desc, latitude, longitude, status, assigned_organization_id, created_at, organizations(name)")
            .not_.is_("latitude", "null")
            .not_.is_("longitude", "null")
            .order("created_at", desc=True)
            .execute()
        )
        return res.data or []
    except Exception as e:
        logger.error(f"Error fetching map reports: {e}")
        return []

def get_signed_evidence_url(photo_storage_path: Optional[str], access_token: Optional[str] = None) -> Optional[str]:
    """
    Generates a secure, time-limited signed URL (60 mins) to view evidence image from private bucket.
    """
    if not photo_storage_path:
        return None
    client = get_authenticated_client(access_token)
    if not client:
        return None

    try:
        res = client.storage.from_(STORAGE_BUCKET).create_signed_url(photo_storage_path, 3600)
        if isinstance(res, dict) and "signedURL" in res:
            return res["signedURL"]
        elif hasattr(res, "signed_url"):
            return res.signed_url
        return None
    except Exception as e:
        logger.debug(f"Could not generate signed URL: {e}")
        return None
