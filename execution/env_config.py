import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def get_env_var(key: str, default: str = "") -> str:
    """Retrieve environment variable, falling back to default or empty string."""
    return os.environ.get(key, default).strip()

# Supabase Credentials
SUPABASE_URL = get_env_var("SUPABASE_URL")
SUPABASE_ANON_KEY = get_env_var("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = get_env_var("SUPABASE_SERVICE_ROLE_KEY")

# AI Service Credentials
GEMINI_API_KEY = get_env_var("GEMINI_API_KEY")
GEMINI_MODEL = get_env_var("GEMINI_MODEL", "gemini-flash-latest")

# Platform Admin Access Passcode
ADMIN_ACCESS_KEY = get_env_var("ADMIN_ACCESS_KEY", "civicsync-admin-secret-2026")

# Demo Accounts
DEMO_CREDENTIALS = {
    "RESIDENT": {
        "email": get_env_var("DEMO_RESIDENT_EMAIL", "resident@civicsync.demo"),
        "password": get_env_var("DEMO_RESIDENT_PASSWORD", "DemoResident#2026"),
        "name": "Citizen Ravi (Resident)",
        "role": "RESIDENT"
    },
    "AUTHORITY_GCC": {
        "email": get_env_var("DEMO_GCC_EMAIL", "authority.gcc@civicsync.demo"),
        "password": get_env_var("DEMO_GCC_PASSWORD", "DemoAuthority#GCC2026"),
        "name": "Engineer Sundar (GCC Roads)",
        "role": "AUTHORITY",
        "org_name": "Greater Chennai Corporation (Roads Dept)"
    },
    "AUTHORITY_CMWSSB": {
        "email": get_env_var("DEMO_CMWSSB_EMAIL", "authority.cmwssb@civicsync.demo"),
        "password": get_env_var("DEMO_CMWSSB_PASSWORD", "DemoAuthority#CMWSSB2026"),
        "name": "Inspector Anand (CMWSSB Water)",
        "role": "AUTHORITY",
        "org_name": "Chennai Metro Water (CMWSSB)"
    },
    "ADMIN": {
        "email": get_env_var("DEMO_ADMIN_EMAIL", "admin@civicsync.demo"),
        "password": get_env_var("DEMO_ADMIN_PASSWORD", "DemoAdmin#Platform2026"),
        "name": "Platform Administrator",
        "role": "ADMIN"
    }
}

# Routing Service (Optional)
OPENROUTESERVICE_API_KEY = get_env_var("OPENROUTESERVICE_API_KEY")

def is_supabase_configured() -> bool:
    """Returns True if minimum public Supabase credentials are set."""
    return bool(SUPABASE_URL and SUPABASE_ANON_KEY)
