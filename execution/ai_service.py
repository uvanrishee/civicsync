import logging
from typing import Dict, Any, Optional, Tuple
from datetime import date, datetime
from execution.env_config import GEMINI_API_KEY, GEMINI_MODEL
from execution.projects_service import get_project_by_id, get_project_updates, get_published_projects
from execution.reports_service import get_resident_reports
from execution.geo_utils import haversine_km

logger = logging.getLogger(__name__)

def test_gemini_connection() -> Dict[str, Any]:
    """Smoke test to verify Gemini API key and model availability."""
    if not GEMINI_API_KEY:
        return {"success": False, "message": "GEMINI_API_KEY is not configured in .env"}

    try:
        # Try google.genai first (new SDK), fallback to google.generativeai
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents="Ping. Respond with 'CivicSync AI Ready'."
            )
            text = response.text or ""
            return {"success": True, "message": f"Gemini connection verified! Model: {GEMINI_MODEL}. Response: {text.strip()}"}
        except ImportError:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel(GEMINI_MODEL)
            response = model.generate_content("Ping. Respond with 'CivicSync AI Ready'.")
            return {"success": True, "message": f"Gemini connection verified! Model: {GEMINI_MODEL}. Response: {response.text.strip()}"}
    except Exception as e:
        return {"success": False, "message": f"Gemini API test failed: {e}"}

def generate_deterministic_fallback(project: Dict[str, Any], updates: list) -> str:
    """
    Structured, factual non-AI summary generated deterministically from database fields.
    Engaged whenever Gemini API is unavailable or quota is exceeded.
    """
    title = project.get("title", "Unknown Project")
    org = project.get("organizations", {}).get("name") if isinstance(project.get("organizations"), dict) else "Public Authority"
    status = project.get("status", "N/A")
    category = project.get("category", "N/A")
    location = project.get("location_name", "Chennai")
    stretch = project.get("road_stretch_desc", "Specific corridor not recorded")
    start = project.get("planned_start_date", "N/A")
    orig_end = project.get("original_estimated_end_date", "N/A")
    curr_end = project.get("current_estimated_end_date", "N/A")
    disruption = project.get("expected_disruption", "No specific disruption notes recorded.")

    # Calculate date differences
    today = date.today()
    days_note = ""
    try:
        target_d = datetime.strptime(str(curr_end), "%Y-%m-%d").date()
        diff = (target_d - today).days
        if diff > 0:
            days_note = f"**{diff} days remaining** until target completion."
        elif diff == 0:
            days_note = "Target completion is **today**."
        else:
            days_note = f"Target completion date passed **{abs(diff)} days ago** (awaiting progress update)."
    except Exception:
        days_note = "Target schedule pending update."

    update_text = "No recent updates logged."
    if updates:
        latest = updates[-1]
        u_date = str(latest.get("created_at", ""))[:10]
        u_note = latest.get("update_note", "")
        update_text = f"*{u_date}*: {u_note}"

    fallback_md = f"""
> **[Verified Database Snapshot — AI Assistant Offline]**
> *Source: CivicSync Public Works Registry*

### {title}
- **Managing Authority:** {org}
- **Sector / Category:** `{category}`
- **Location:** {location} ({stretch})
- **Current Status:** `{status}`
- **Schedule:** Started `{start}` | Target Completion `{curr_end}` ({days_note})
- **Recorded Disruption:** {disruption}
- **Latest Official Progress:** {update_text}

*Note: This information is pulled directly from registered database records.*
"""
    return fallback_md.strip()

def ask_project_assistant(project_id: str, user_question: str, access_token: Optional[str] = None) -> str:
    """
    Context-grounded AI assistant for a specific registered infrastructure project.
    Strictly forbids hallucinating dates, closures, or safety guarantees.
    """
    project = get_project_by_id(project_id, access_token)
    if not project:
        return "Sorry, I could not locate the details for this project in the registry."

    updates = get_project_updates(project_id, access_token)

    # If Gemini API key is missing, return deterministic fallback immediately
    if not GEMINI_API_KEY:
        return generate_deterministic_fallback(project, updates)

    # Compute deterministic facts
    today = date.today()
    planned_end = project.get("current_estimated_end_date")
    schedule_math = ""
    try:
        end_d = datetime.strptime(str(planned_end), "%Y-%m-%d").date()
        diff = (end_d - today).days
        if diff > 0:
            schedule_math = f"Today is {today}. Target completion is {planned_end} ({diff} days from today)."
        else:
            schedule_math = f"Today is {today}. Target completion was {planned_end} ({abs(diff)} days in the past)."
    except Exception:
        schedule_math = f"Today is {today}."

    updates_summary = "\n".join([
        f"- {str(u.get('created_at', ''))[:10]}: [Status: {u.get('status_at_update')}] {u.get('update_note')} (Revised end: {u.get('revised_estimated_end_date') or 'None'})"
        for u in updates
    ]) or "No progress updates recorded yet."

    context_prompt = f"""
You are CivicSync's AI Disruption Assistant for public works in Chennai.
Answer the resident's question ONLY using the factual record provided below.

STRICT GROUNDING RULES:
1. State facts directly from the provided record.
2. If the user asks for information not in the record (e.g. why there is a delay, exact lane closure hours, whether the road is safe to drive, detour directions), you MUST explicitly state that the official record does not specify this.
3. NEVER fabricate dates, contractor names, detour routes, or road safety guarantees.
4. Keep the answer concise, polite, and helpful for a Chennai commuter.

PROJECT FACT SHEET:
- Project Title: {project.get('title')}
- Registering Organization: {project.get('organizations', {}).get('name') if isinstance(project.get('organizations'), dict) else 'Chennai Civic Body'}
- Category: {project.get('category')}
- Location: {project.get('location_name')} ({project.get('road_stretch_desc') or 'Stretch not specified'})
- Planned Start Date: {project.get('planned_start_date')}
- Original Target Completion: {project.get('original_estimated_end_date')}
- Current Target Completion: {project.get('current_estimated_end_date')}
- Schedule Calculation: {schedule_math}
- Status: {project.get('status')}
- Declared Disruption: {project.get('expected_disruption') or 'None recorded'}
- Data Origin: {project.get('data_origin')}
- Chronological Updates:
{updates_summary}

USER QUESTION:
{user_question}
"""

    try:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=context_prompt
            )
            return response.text.strip()
        except ImportError:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel(GEMINI_MODEL)
            response = model.generate_content(context_prompt)
            return response.text.strip()
    except Exception as e:
        logger.warning(f"Gemini API call failed: {e}. Falling back to deterministic summary.")
        return generate_deterministic_fallback(project, updates)


def generate_general_deterministic_fallback(
    user_question: str,
    reports: list,
    nearest_proj: Optional[Tuple[float, Dict[str, Any]]],
    nearby_projs: list,
    all_projects: list,
    home_lat: Optional[float],
    home_lon: Optional[float]
) -> str:
    """Deterministic fallback for general queries when Gemini API is unavailable."""
    q_low = user_question.lower()
    
    # 1. Reports count inquiry
    if any(k in q_low for k in ["report", "complaint", "complained", "filed", "solve", "solved", "status"]):
        total = len(reports)
        res_count = len([r for r in reports if r.get("status") == "RESOLVED"])
        in_prog = len([r for r in reports if r.get("status") == "IN_PROGRESS"])
        ack = len([r for r in reports if r.get("status") == "ACKNOWLEDGED"])
        pend = len([r for r in reports if r.get("status") == "PENDING_REVIEW"])
        
        lines = [
            f"> **[Verified Database Snapshot — AI Assistant Offline]**\n",
            f"### 📋 Your Civic Reports Summary",
            f"- **Total Reports Filed:** **{total}**",
            f"- **Resolved:** **{res_count}**",
            f"- **In Progress:** **{in_prog}**",
            f"- **Acknowledged:** **{ack}**",
            f"- **Pending Review:** **{pend}**\n"
        ]
        if reports:
            lines.append("#### Your Recent Submissions:")
            for r in reports[:4]:
                cat = r.get("category", "Issue").replace("_", " ").title()
                stat = r.get("status", "PENDING_REVIEW")
                loc = r.get("location_desc", "Chennai")
                lines.append(f"- **{cat}** at *{loc}* → `{stat}`")
        return "\n".join(lines)

    # 2. Nearest work / proximity inquiry
    if any(k in q_low for k in ["near", "nearest", "close", "closest", "home", "distance", "km", "around"]):
        if home_lat is None or home_lon is None:
            return (
                "> **[Verified Database Snapshot — AI Assistant Offline]**\n\n"
                "📍 **Home Location Not Set:** You haven't saved a neighbourhood location yet. "
                "Please drop a pin on the Home page or Explore Map to calculate distances to nearby public works."
            )
        if nearest_proj:
            d_km, p = nearest_proj
            p_title = p.get("title", "Public Work")
            p_org = p.get("organizations", {}).get("name") if isinstance(p.get("organizations"), dict) else "Chennai Authority"
            p_stat = p.get("status", "IN_PROGRESS")
            p_end = p.get("current_estimated_end_date", "TBD")
            p_dis = p.get("expected_disruption", "Lane advisory in effect.")
            
            lines = [
                f"> **[Verified Database Snapshot — AI Assistant Offline]**\n",
                f"### 📍 Nearest Infrastructure Work to Your Location",
                f"- **Project:** **{p_title}**",
                f"- **Distance from Your Home:** **{d_km:.2f} km**",
                f"- **Managing Body:** {p_org}",
                f"- **Status:** `{p_stat}`",
                f"- **Target Completion:** `{p_end}`",
                f"- **Expected Disruption:** {p_dis}\n",
                f"#### Other Works Within 5 km ({len(nearby_projs)} total):"
            ]
            for d, nb in nearby_projs[:4]:
                lines.append(f"- **{nb.get('title')}** — {d:.1f} km away (`{nb.get('status')}`)")
            return "\n".join(lines)

    # Default general city overview
    return (
        f"> **[Verified Database Snapshot — AI Assistant Offline]**\n\n"
        f"### 🏛️ Chennai Public Works Registry Overview\n"
        f"- **Total Active Registered Projects:** **{len(all_projects)}**\n"
        f"- **Your Filed Reports:** **{len(reports)}**\n"
        f"- Explore the interactive map to review road corridors and ongoing utility projects."
    )


def ask_general_assistant(
    user_question: str,
    user_id: Optional[str] = None,
    profile: Optional[Dict[str, Any]] = None,
    access_token: Optional[str] = None
) -> str:
    """
    General CivicSync AI Assistant capable of answering personal queries:
    - How many reports filed vs resolved
    - Distance to the nearest public work from home
    - Works within 5 km radius
    - Chennai infrastructure overview
    """
    # 1. Fetch user reports
    reports = get_resident_reports(user_id, access_token) if user_id else []
    total_reports = len(reports)
    resolved_count = len([r for r in reports if r.get("status") == "RESOLVED"])
    in_progress_count = len([r for r in reports if r.get("status") == "IN_PROGRESS"])
    acknowledged_count = len([r for r in reports if r.get("status") == "ACKNOWLEDGED"])
    pending_count = len([r for r in reports if r.get("status") == "PENDING_REVIEW"])

    reports_summary_lines = []
    for r in reports:
        cat = r.get("category", "Issue").replace("_", " ").title()
        loc = r.get("location_desc", "Location unstated")
        stat = r.get("status", "PENDING_REVIEW")
        date_str = str(r.get("created_at", ""))[:10]
        res_note = r.get("resolution_summary") or "Awaiting resolution"
        reports_summary_lines.append(
            f"- [{stat}] {cat} at '{loc}' (Filed: {date_str}) | Resolution note: {res_note}"
        )
    reports_text = "\n".join(reports_summary_lines) if reports_summary_lines else "No civic problem reports filed yet by this resident."

    # 2. Fetch all published projects and compute proximity
    all_projects = get_published_projects(access_token)
    home_lat = profile.get("home_latitude") if profile else None
    home_lon = profile.get("home_longitude") if profile else None

    proj_with_dist = []
    if home_lat is not None and home_lon is not None:
        try:
            h_lat = float(home_lat)
            h_lon = float(home_lon)
            for p in all_projects:
                p_lat = p.get("latitude")
                p_lon = p.get("longitude")
                if p_lat is not None and p_lon is not None:
                    try:
                        d = haversine_km(h_lat, h_lon, float(p_lat), float(p_lon))
                        proj_with_dist.append((d, p))
                    except (ValueError, TypeError):
                        pass
            proj_with_dist.sort(key=lambda x: x[0])
        except (ValueError, TypeError):
            pass

    nearest_proj = proj_with_dist[0] if proj_with_dist else None
    nearby_projs = [(d, p) for d, p in proj_with_dist if d <= 5.0]

    # Proximity description text
    if home_lat is not None and home_lon is not None:
        home_desc = f"Saved Coordinates: ({float(home_lat):.4f}, {float(home_lon):.4f})"
        if nearest_proj:
            nd, np = nearest_proj
            nearest_desc = (
                f"'{np.get('title')}' managed by {np.get('organizations', {}).get('name') if isinstance(np.get('organizations'), dict) else 'Authority'}, "
                f"located exactly {nd:.2f} km away (approx {int(nd*1000)} meters). Status: {np.get('status')}. Expected disruption: {np.get('expected_disruption') or 'None noted'}."
            )
        else:
            nearest_desc = "No geo-tagged projects currently available."
        nearby_desc = "\n".join([
            f"- {p.get('title')} ({d:.2f} km away) — Status: {p.get('status')}, Target: {p.get('current_estimated_end_date')}"
            for d, p in nearby_projs
        ]) or "No active public works registered within 5 km of home."
    else:
        home_desc = "Home location NOT set yet. Resident has not dropped a neighbourhood pin."
        nearest_desc = "Cannot compute distance because resident has not saved their home coordinates."
        nearby_desc = "Cannot compute nearby works without home coordinates."

    city_projects_summary = "\n".join([
        f"- {p.get('title')} ({p.get('location_name')}) — Org: {p.get('organizations', {}).get('name') if isinstance(p.get('organizations'), dict) else 'Civic Body'}, Status: {p.get('status')}, Target: {p.get('current_estimated_end_date')}"
        for p in all_projects[:6]
    ])

    if not GEMINI_API_KEY:
        return generate_general_deterministic_fallback(
            user_question, reports, nearest_proj, nearby_projs, all_projects, home_lat, home_lon
        )

    system_prompt = f"""
You are CivicSync's AI Civic Assistant for Chennai residents.
You have direct, verified access to this specific resident's personal account data and the city's public works registry.

STRICT GROUNDING RULES:
1. Answer the resident's question directly, accurately, and politely using ONLY the facts provided below.
2. If the resident asks about their complaints/reports (e.g. how many filed, how many solved/in-progress):
   - Cite the exact numbers: Total filed ({total_reports}), Resolved ({resolved_count}), In Progress ({in_progress_count}), Acknowledged ({acknowledged_count}), Pending ({pending_count}).
   - Mention the specific issue categories or locations if relevant.
3. If the resident asks about the nearest public work from their home:
   - Cite the exact nearest project name and the calculated distance in kilometers and meters ({nearest_desc}).
   - If they haven't saved a home location, politely advise them to drop a pin on the Home or Corridor Map page.
4. If they ask about works around their area (within 5 km), list the nearby works from the record.
5. NEVER fabricate project dates, complaint numbers, or safety assurances.
6. Keep answers concise, clear, and formatted with clean markdown bullets.

VERIFIED RESIDENT & CITY CONTEXT:
Resident Name: {profile.get('display_name', 'Resident') if profile else 'Resident'}
Home Neighbourhood: {home_desc}

1. RESIDENT'S FILED COMPLAINTS & REPORTS:
- Total Complaints Filed: {total_reports}
- Resolved: {resolved_count}
- In Progress: {in_progress_count}
- Acknowledged: {acknowledged_count}
- Pending Review: {pending_count}
Details of Filed Reports:
{reports_text}

2. NEIGHBOURHOOD PROXIMITY TO PUBLIC WORKS:
- Nearest Registered Public Work: {nearest_desc}
- Active Works Within 5 km Radius:
{nearby_desc}

3. CHENNAI ACTIVE INFRASTRUCTURE REGISTRY (Total: {len(all_projects)} projects):
{city_projects_summary}

USER QUESTION:
{user_question}
"""

    try:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=system_prompt
            )
            return response.text.strip()
        except ImportError:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel(GEMINI_MODEL)
            response = model.generate_content(system_prompt)
            return response.text.strip()
    except Exception as e:
        logger.warning(f"Gemini API call failed for general assistant: {e}. Using deterministic fallback.")
        return generate_general_deterministic_fallback(
            user_question, reports, nearest_proj, nearby_projs, all_projects, home_lat, home_lon
        )

