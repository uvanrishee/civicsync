import logging
from typing import Optional
from supabase import create_client, Client
from execution.env_config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY

logger = logging.getLogger(__name__)

def get_anon_client() -> Optional[Client]:
    """
    Creates and returns a Supabase client using public ANON key.
    Safe for frontend and public unauthenticated or resident operations.
    """
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        logger.warning("Supabase URL or ANON Key is not configured.")
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    except Exception as e:
        logger.error(f"Failed to create anon Supabase client: {e}")
        return None

def get_service_role_client() -> Optional[Client]:
    """
    Creates and returns a Supabase client with the SERVICE_ROLE key.
    STRICT SECURITY RULE: Used ONLY for offline CLI database seeding, 
    migrations, or automated backend tests. NEVER exposed in Streamlit UI pages.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        logger.warning("Supabase URL or SERVICE_ROLE Key is not configured.")
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    except Exception as e:
        logger.error(f"Failed to create service role Supabase client: {e}")
        return None

def get_authenticated_client(access_token: Optional[str] = None) -> Optional[Client]:
    """
    Returns a client configured with the active user's access token,
    ensuring PostgreSQL Row Level Security (RLS) policies evaluate auth.uid().
    """
    client = get_anon_client()
    if client and access_token:
        try:
            client.postgrest.auth(access_token)
        except Exception as e:
            logger.debug(f"Note setting postgrest auth header: {e}")
    return client
