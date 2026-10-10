# CivicSync

**A civic coordination and public works intelligence platform for Chennai, Tamil Nadu.**

CivicSync bridges the gap between government authorities and residents by providing a transparent, real-time view of public infrastructure works across the city. Residents can discover nearby disruptions, report issues with geo-tagged evidence, and receive AI-assisted guidance — while authorities manage projects, triage incoming reports, and maintain accountability through a structured workflow.

---

## Overview

Urban infrastructure works — road resurfacing, stormwater drainage, water pipeline excavation, metro construction — routinely disrupt daily life without adequate public communication. CivicSync addresses this by:

- Giving residents a spatial, map-based view of all active and planned works in their neighbourhood.
- Enabling accountable issue reporting that routes directly to the responsible government body.
- Providing a context-grounded AI assistant that answers questions about specific projects or a resident's personal report history, based strictly on live database facts.
- Giving authorities a structured portal to register works, post progress updates, and triage citizen reports.
- Giving platform administrators visibility and control over organisational approvals and the system audit log.

---

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| Web Framework | Streamlit |
| Interactive Map | Folium, streamlit-folium |
| Authentication and Database | Supabase (PostgreSQL with Row Level Security) |
| File Storage | Supabase Storage (private evidence bucket) |
| AI Assistant | Google Gemini (gemini-2.5-flash) with deterministic fallback |
| Deployment Target | Streamlit Community Cloud |

---

## Project Structure

```
civicsync/
├── app.py                    # Application entry point and authentication
├── pages/
│   ├── 1_Explore_Map.py      # Interactive Chennai works map with proximity filter
│   ├── 2_Report_Issue.py     # Geo-tagged citizen issue reporting with photo upload
│   ├── 3_My_Reports.py       # Personal report history and status tracking
│   ├── 4_AI_Assistant.py     # Gemini-powered assistant (project and general queries)
│   ├── 5_Authority_Portal.py # Authority project management and report triage
│   └── 6_Admin_Portal.py     # Platform administration and audit log
├── execution/
│   ├── ai_service.py         # Gemini API integration with deterministic fallback
│   ├── auth_service.py       # Supabase Auth (sign-up, sign-in, email verification)
│   ├── projects_service.py   # Project CRUD and search
│   ├── reports_service.py    # Report submission, retrieval, and status updates
│   ├── supabase_client.py    # Supabase client initialisation
│   ├── env_config.py         # Environment variable loader
│   └── geo_utils.py          # Haversine distance and proximity calculations
├── ui/
│   ├── components.py         # Reusable UI components
│   ├── map_view.py           # Folium map builder and pin-drop utilities
│   ├── nav.py                # Sidebar navigation and session state
│   └── styles.py             # Custom CSS injection
├── requirements.txt
├── .env.example
└── .streamlit/config.toml
```

---

## Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/uvanrishee/civicsync.git
cd civicsync
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in the following values:

| Variable | Description |
|---|---|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase public anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (used only for database seeding) |
| `GEMINI_API_KEY` | API key from [Google AI Studio](https://aistudio.google.com) |
| `GEMINI_MODEL` | `gemini-2.5-flash` |
| `ADMIN_ACCESS_KEY` | Passcode to access the Admin Portal |

### 3. Set Up the Supabase Database

In your Supabase Dashboard, open the SQL Editor and run the schema setup script. This creates:

- All application tables: `profiles`, `organizations`, `projects`, `reports`, `report_updates`, `project_updates`, `memberships`, `audit_log`, and `home_locations`.
- Non-recursive Row Level Security (RLS) policies using `SECURITY DEFINER` helper functions.
- Anti-escalation and immutability triggers.
- A private storage bucket (`civicsync-evidence`) for photo evidence.

### 4. Run the Application

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## Demo Accounts

The following pre-confirmed accounts are available for evaluation without requiring email verification:

| Role | Email | Password |
|---|---|---|
| Resident | resident@civicsync.demo | DemoResident#2026 |
| GCC Roads Authority | authority.gcc@civicsync.demo | DemoAuthority#GCC2026 |
| Metro Water (CMWSSB) | authority.cmwssb@civicsync.demo | DemoAuthority#CMWSSB2026 |
| Platform Administrator | admin@civicsync.demo | DemoAdmin#Platform2026 |

These can be accessed directly from the Demo Fast-Track tab on the landing page, bypassing the standard sign-in form.

---

## Features by Role

### Resident

- Explore an interactive Chennai map centred on the resident's home neighbourhood, with active works marked by category (roads, drainage, water, metro).
- Set a home location via pin-drop and view all works within a configurable proximity radius.
- Submit geo-tagged issue reports with optional photo evidence, automatically routed to the responsible authority.
- Track all personal reports and their resolution status over time.
- Query the AI assistant about specific projects, nearest active works, or personal report statistics.

### Authority

- Register new public works projects with location, schedule, and category details.
- Post progress updates visible to the public on the map.
- View and respond to citizen reports assigned to their organisation.
- Update report status through a defined workflow: Pending, In Review, In Progress, Resolved, Closed.

### Platform Administrator

- Approve or reject new organisation registrations.
- Review the immutable audit log of all system actions.
- Access protected by a passcode barrier separate from standard authentication.

---

## AI Assistant

The assistant operates in two modes:

- **Project mode:** Answers questions about a selected public works project using stored database facts — location, schedule, status, and progress updates.
- **General mode:** Answers personal queries such as total reports submitted, reports resolved, and distance to the nearest active work from the resident's saved home location.

If the Gemini API is unavailable due to demand spikes, the assistant automatically falls back to a structured, database-driven summary. No response fabricates information beyond what is present in the database.

---

## Deployment

The application is designed for deployment to Streamlit Community Cloud:

1. Connect this repository to your Streamlit Cloud account.
2. Set the main file path to `app.py`.
3. Under Settings, open the Secrets panel and paste the contents of your `.env` file.
4. Deploy.

No build step is required. All dependencies are declared in `requirements.txt`.

---

## Data Notes

- All geographic data is scoped to the Chennai Metropolitan Area.
- Seeded demonstration projects are explicitly tagged as simulated for evaluation purposes.
- The AI assistant is strictly grounded to stored database facts and does not generate speculative or fabricated information.
