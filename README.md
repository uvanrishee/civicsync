# CivicSync — Chennai Public Works & Disruption Platform

> **Understand public works. Navigate disruptions. Improve civic accountability.**

CivicSync is an open-source civic coordination and spatial disruption intelligence platform designed for Chennai, Tamil Nadu, India. It connects public works execution with resident mobility:
- 🗺️ **Interactive Chennai Works Registry:** Real-time map-based discovery of active and planned roadworks, stormwater drainage, water/sewerage pipeline excavation, and metro rail construction.
- 🤖 **Context-Grounded AI Assistant:** Natural language disruption guidance powered by Google Gemini, strictly constrained to stored database facts and calculating schedules deterministically.
- 📢 **Accountable Citizen Problem Reporting:** Geo-tagged issue reporting with photo evidence routing directly into the responsible authority's triage inbox, with transparent audit history.

---

## 🏗️ Architecture & Technology Stack

The project adheres to a strict 3-layer architecture:
- **Layer 1: Directives (`directives/`):** Operational Standard Operating Procedures (SOPs) for schema migrations, data seeding, and deployment verification.
- **Layer 2: Orchestration:** Multi-role user navigation, session state management, and strict access routing.
- **Layer 3: Deterministic Execution (`execution/`):** Testable Python services handling Supabase PostgreSQL access, RLS policies, private file storage, and Gemini grounding.

| Component | Technology | Responsibility |
|---|---|---|
| **Language** | Python 3.10+ | Business logic, data transformations, API integrations |
| **Web UI** | Streamlit | Responsive multi-page web application |
| **Interactive Map** | Folium + `streamlit-folium` | Chennai map, category-coded markers, click callbacks |
| **Auth & Database** | Supabase (PostgreSQL) | Identity, relational data, non-recursive RLS, triggers |
| **Evidence Storage** | Supabase Storage | Private bucket (`civicsync-evidence`) with signed URLs |
| **AI Assistant** | Google Gemini (`gemini-2.5-flash`) | Context-grounded Q&A with deterministic fallback |
| **Hosting** | Streamlit Community Cloud | Public deployment target |

---

## 🚀 Quickstart & Local Setup

### 1. Clone & Install Dependencies

```bash
git clone https://github.com/your-username/bB_hackathon.git
cd bB_hackathon

# Install required packages
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Fill in your credentials in `.env`:
- `SUPABASE_URL`: Your Supabase Project URL.
- `SUPABASE_ANON_KEY`: Your Supabase Public Anon Key.
- `SUPABASE_SERVICE_ROLE_KEY`: Service role key (used only for offline seeding).
- `GEMINI_API_KEY`: API Key from [Google AI Studio](https://aistudio.google.com).
- `GEMINI_MODEL`: `gemini-2.5-flash`.
- `ADMIN_ACCESS_KEY`: `civicsync-admin-secret-2026` (Passcode to unlock Admin Portal).

### 3. Setup Supabase Database & Security Policies

1. Open your **Supabase Dashboard -> SQL Editor**.
2. Open [`directives/setup_database.md`](directives/setup_database.md) and copy the complete SQL script.
3. Paste and run the script in the SQL editor. This creates:
   - All 9 application tables (`profiles`, `organizations`, `projects`, `reports`, etc.).
   - Non-recursive `SECURITY DEFINER` helper functions (`is_admin`, `has_org_role`).
   - Anti-escalation and immutability triggers.
   - Comprehensive Row Level Security (RLS) policies.
   - Private Storage bucket `civicsync-evidence`.

### 4. Seed Chennai Demonstration Data

Run the offline seeding CLI script from your terminal:

```bash
python execution/seed_data.py
```

This populates:
- **Organizations:** Greater Chennai Corporation (Roads Dept), Chennai Metro Water (CMWSSB), CMRL, TANGEDCO.
- **Pre-Confirmed Demo Accounts:**
  - Citizen: `resident@civicsync.demo` (Password: `DemoResident#2026`)
  - GCC Roads Authority: `authority.gcc@civicsync.demo` (Password: `DemoAuthority#GCC2026`)
  - CMWSSB Water Authority: `authority.cmwssb@civicsync.demo` (Password: `DemoAuthority#CMWSSB2026`)
  - Platform Administrator: `admin@civicsync.demo` (Password: `DemoAdmin#Platform2026`)
- **Chennai Public Works:** 5 realistic projects across Anna Salai, T. Nagar, OMR, Vadapalani, and Velachery.
- **Citizen Reports:** 3 sample issue reports demonstrating pending, in-progress, and resolved workflows.

### 5. Launch Application

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## ⚡ Demonstration & Evaluation Fast-Track (For Judges)

To make evaluation effortless without requiring manual inbox email confirmations:
1. Open the app in your browser.
2. In the sidebar or on the landing page's **Demo Fast-Track** tab, click any persona:
   - **👤 Resident (Ravi):** Test exploring the map, asking the AI assistant, submitting problem reports with photos, and tracking status.
   - **🏛️ GCC Roads Dept:** Test registering a public work, adding progress updates, and triaging assigned citizen reports.
   - **💧 Metro Water (CMWSSB):** Test water pipeline project management and drainage issue resolutions.
   - **🛡️ Platform Admin:** Test organization approvals and inspect the immutable audit log (Passcode: `civicsync-admin-secret-2026`).

---

## 🧪 Security & Quality Verification

Run automated verification scripts directly:

```bash
# Verify AI Assistant Connectivity
python execution/test_ai_smoke.py

# Run Automated Negative Security Audit (RLS & Triggers)
python execution/test_security_negative.py
```

---

## ☁️ Deployment

See [`directives/verify_deployment.md`](directives/verify_deployment.md) for full Streamlit Community Cloud deployment steps and secrets configuration.

---

## 📍 Data Provenance & Limitations

- **Geographic Pilot:** Focused exclusively on the Chennai Metropolitan Area.
- **Simulated Records:** All seeded demonstration projects are explicitly tagged with `[DEMO - SIMULATED FOR EVALUATION]`.
- **Grounded AI:** The assistant strictly answers from stored database facts. It never fabricates road closures or safety assurances. If the Gemini API is offline, a deterministic database summary card is automatically provided.
