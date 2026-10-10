import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime
from execution.supabase_client import get_anon_client, get_authenticated_client

logger = logging.getLogger(__name__)

def get_all_organizations(access_token: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves all approved organizations in Chennai."""
    client = get_authenticated_client(access_token)
    if not client:
        return []
    try:
        res = client.table("organizations").select("*").eq("status", "APPROVED").order("name").execute()
        return res.data or []
    except Exception as e:
        logger.error(f"Error fetching organizations: {e}")
        return []

def get_published_projects(
    access_token: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetches published infrastructure projects with their registering organization details.
    """
    client = get_authenticated_client(access_token)
    if not client:
        return []

    try:
        query = client.table("projects").select("*, organizations(name, org_type)").eq("publication_status", "PUBLISHED")

        if category and category != "ALL":
            query = query.eq("category", category)
        if status and status != "ALL":
            query = query.eq("status", status)

        res = query.order("created_at", desc=True).execute()
        projects = res.data or []

        if search:
            search_lower = search.lower()
            projects = [
                p for p in projects
                if search_lower in (p.get("title") or "").lower()
                or search_lower in (p.get("location_name") or "").lower()
                or search_lower in (p.get("description") or "").lower()
                or search_lower in (p.get("road_stretch_desc") or "").lower()
            ]

        return projects
    except Exception as e:
        logger.error(f"Error fetching published projects: {e}")
        return []

def get_project_by_id(project_id: str, access_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetches single project by ID with organization details."""
    client = get_authenticated_client(access_token)
    if not client:
        return None

    try:
        res = client.table("projects").select("*, organizations(*)").eq("id", project_id).limit(1).execute()
        if res.data:
            return res.data[0]
        return None
    except Exception as e:
        logger.error(f"Error fetching project {project_id}: {e}")
        return None

def get_project_updates(project_id: str, access_token: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetches chronological progress timeline for a project."""
    client = get_authenticated_client(access_token)
    if not client:
        return []

    try:
        res = client.table("project_updates").select("*").eq("project_id", project_id).order("created_at", desc=False).execute()
        return res.data or []
    except Exception as e:
        logger.error(f"Error fetching updates for project {project_id}: {e}")
        return []

def create_project(project_data: Dict[str, Any], access_token: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Validates and registers a new public works project in Supabase.
    """
    client = get_authenticated_client(access_token)
    if not client:
        return False, "Database client is not available.", None

    # Validate required fields
    required = ["title", "description", "category", "location_name", "planned_start_date", "original_estimated_end_date", "organization_id", "created_by"]
    for field in required:
        if not project_data.get(field):
            return False, f"Missing required field: {field}", None

    # Date validation
    try:
        start_d = datetime.strptime(str(project_data["planned_start_date"]), "%Y-%m-%d").date()
        end_d = datetime.strptime(str(project_data["original_estimated_end_date"]), "%Y-%m-%d").date()
        if end_d < start_d:
            return False, "Estimated end date cannot be earlier than planned start date.", None
    except Exception as e:
        return False, f"Invalid date format (must be YYYY-MM-DD): {e}", None

    # Default current estimate
    if "current_estimated_end_date" not in project_data:
        project_data["current_estimated_end_date"] = project_data["original_estimated_end_date"]

    try:
        res = client.table("projects").insert(project_data).execute()
        if res.data:
            return True, "Project successfully registered!", res.data[0]
        return False, "Failed to insert project record.", None
    except Exception as e:
        logger.error(f"Error inserting project: {e}")
        return False, f"Database error creating project: {e}", None

def add_project_update(
    project_id: str,
    author_id: str,
    status_at_update: str,
    update_note: str,
    revised_estimated_end_date: Optional[str] = None,
    reason_for_change: Optional[str] = None,
    access_token: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Appends a progress update event and updates current project status/estimate.
    """
    client = get_authenticated_client(access_token)
    if not client:
        return False, "Database client is not available."

    try:
        update_payload = {
            "project_id": project_id,
            "author_id": author_id,
            "status_at_update": status_at_update,
            "update_note": update_note.strip(),
            "revised_estimated_end_date": revised_estimated_end_date,
            "reason_for_change": reason_for_change.strip() if reason_for_change else None
        }
        res_up = client.table("project_updates").insert(update_payload).execute()
        if not res_up.data:
            return False, "Could not record update."

        # Update projects table summary fields
        project_summary_update: Dict[str, Any] = {
            "status": status_at_update,
            "updated_at": "now()"
        }
        if revised_estimated_end_date:
            project_summary_update["current_estimated_end_date"] = revised_estimated_end_date

        client.table("projects").update(project_summary_update).eq("id", project_id).execute()
        return True, "Project progress update recorded successfully!"
    except Exception as e:
        logger.error(f"Error adding project update: {e}")
        return False, f"Database error adding update: {e}"

def get_organization_projects(organization_id: str, access_token: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetches all projects managed by an authority's organization."""
    client = get_authenticated_client(access_token)
    if not client:
        return []

    try:
        res = client.table("projects").select("*").eq("organization_id", organization_id).order("created_at", desc=True).execute()
        return res.data or []
    except Exception as e:
        logger.error(f"Error fetching org projects: {e}")
        return []
