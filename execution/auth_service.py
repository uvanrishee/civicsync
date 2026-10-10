import logging
from typing import Dict, Any, Optional, Tuple
from execution.supabase_client import get_anon_client, get_service_role_client
from execution.env_config import DEMO_CREDENTIALS

logger = logging.getLogger(__name__)

def sign_in_user(email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Authenticates user via Supabase Auth.
    Returns: (success: bool, message: str, session_data: Optional[Dict])
    """
    client = get_anon_client()
    if not client:
        return False, "Database client is not configured. Please check SUPABASE_URL and SUPABASE_ANON_KEY.", None

    try:
        response = client.auth.sign_in_with_password({
            "email": email.strip(),
            "password": password
        })
        user = response.user
        session = response.session

        if not user or not session:
            return False, "Invalid authentication response from server.", None

        # Fetch profile
        profile = get_user_profile(user.id, session.access_token)
        membership = get_user_membership(user.id, session.access_token)

        session_payload = {
            "user_id": user.id,
            "email": user.email,
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "profile": profile,
            "membership": membership
        }
        return True, "Login successful", session_payload

    except Exception as e:
        err_msg = str(e)
        logger.warning(f"Sign in failed for {email}: {err_msg}")
        if "Email not confirmed" in err_msg or "email_not_confirmed" in err_msg:
            return False, "Email not verified. Please check your inbox and click the verification link before logging in.", None
        elif "Invalid login credentials" in err_msg or "invalid_grant" in err_msg:
            return False, "Invalid email or password. Please verify your credentials.", None
        return False, f"Sign in failed: {err_msg}", None

def resend_verification_email(email: str) -> Tuple[bool, str]:
    """Requests Supabase to resend the confirmation email for an unverified user."""
    client = get_anon_client()
    if not client:
        return False, "Database client is not configured."
    try:
        client.auth.resend({"type": "signup", "email": email.strip()})
        return True, f"Verification link resent to {email}! Please check your inbox and spam folder."
    except Exception as e:
        err_msg = str(e)
        logger.warning(f"Resend verification failed for {email}: {err_msg}")
        if "rate limit" in err_msg.lower():
            return False, "Email rate limit reached. Please wait a few minutes before requesting another verification email."
        return False, f"Could not resend email: {err_msg}"

def sign_up_user(
    email: str,
    password: str,
    display_name: str,
    role: str = "RESIDENT",
    org_id: Optional[str] = None,
    org_name: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Registers a new user via Supabase Auth.
    Sends an email verification link to the user before they can sign in.
    If role is AUTHORITY and org_id is provided, links organization membership.
    Returns: (success: bool, message: str)
    """
    client = get_anon_client()
    if not client:
        return False, "Database client is not configured."

    try:
        metadata = {
            "display_name": display_name.strip(),
            "role": role
        }
        if org_name:
            metadata["requested_org"] = org_name.strip()
        if org_id:
            metadata["requested_org_id"] = str(org_id)

        # Standard client sign_up triggers the Supabase confirmation email
        response = client.auth.sign_up({
            "email": email.strip(),
            "password": password,
            "options": {
                "data": metadata
            }
        })
        user = response.user
        session = response.session

        if not user:
            return False, "Registration failed: No user returned."

        # If role is AUTHORITY and org_id specified, link organization membership
        if role == "AUTHORITY" and org_id:
            svc_client = get_service_role_client()
            if svc_client:
                try:
                    svc_client.table("organization_memberships").insert({
                        "user_id": user.id,
                        "organization_id": org_id,
                        "role_in_org": "OFFICER",
                        "status": "APPROVED"
                    }).execute()
                    logger.info(f"Linked approved membership for authority {email} to org {org_id}")
                except Exception as mex:
                    logger.warning(f"Failed linking organization membership for {user.id}: {mex}")

        if session is None:
            return True, f"Registration successful! ✉️ A verification email has been sent to **{email}**. Please check your inbox (and spam folder) and click the link to verify your account before logging in."
        else:
            return True, "Account registered successfully! You may now sign in."

    except Exception as e:
        err_msg = str(e)
        logger.error(f"Sign up error: {err_msg}")
        if "already registered" in err_msg.lower() or "already been registered" in err_msg.lower():
            return False, "An account with this email address already exists. Please sign in."
        if "rate limit" in err_msg.lower():
            return False, "Supabase email rate limit reached (max 3/hr on default free tier). Please wait or sign in using a Demo account."
        return False, f"Registration failed: {err_msg}"

def sign_in_demo(persona_key: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Convenience demo login for hackathon evaluation using environment-injected demo credentials.
    """
    if persona_key not in DEMO_CREDENTIALS:
        return False, f"Unknown demo persona: {persona_key}", None

    creds = DEMO_CREDENTIALS[persona_key]
    return sign_in_user(creds["email"], creds["password"])

def get_user_profile(user_id: str, access_token: Optional[str] = None) -> Dict[str, Any]:
    """Retrieves user profile record from public.profiles."""
    client = get_service_role_client() or get_anon_client()
    if not client:
        return {"id": user_id, "display_name": "User", "role": "RESIDENT"}

    try:
        res = client.table("profiles").select("*").eq("id", user_id).limit(1).execute()
        if res.data:
            return res.data[0]
    except Exception as e:
        logger.debug(f"Could not fetch profile for {user_id}: {e}")

    return {"id": user_id, "display_name": "User", "role": "RESIDENT"}

def get_user_membership(user_id: str, access_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves organization membership and linked organization for authority user.
    Uses service-role client to prevent recursive RLS policy loops.
    """
    client = get_service_role_client() or get_anon_client()
    if not client:
        return None

    try:
        res = client.table("organization_memberships").select("*, organizations(*)").eq("user_id", user_id).eq("status", "APPROVED").limit(1).execute()
        if res.data:
            return res.data[0]
    except Exception as e:
        logger.debug(f"Could not fetch membership for {user_id}: {e}")

    return None

def save_home_location(user_id: str, latitude: float, longitude: float) -> Tuple[bool, str]:
    """
    Persists the citizen's home/neighbourhood pin to their profile row.
    Only meaningful for RESIDENT role — call site should guard for role.
    """
    client = get_service_role_client()
    if not client:
        return False, "Database client not available."
    try:
        client.table("profiles").update({
            "home_latitude": latitude,
            "home_longitude": longitude
        }).eq("id", user_id).execute()
        return True, "Location saved."
    except Exception as e:
        logger.error(f"Failed to save home location for {user_id}: {e}")
        return False, f"Could not save location: {e}"

def reload_profile(user_id: str) -> Dict[str, Any]:
    """Re-fetches the latest profile row from DB (e.g., after saving home location)."""
    return get_user_profile(user_id)
