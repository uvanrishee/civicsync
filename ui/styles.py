"""
CivicSync Styling System
Professional civic-tech aesthetic using Navy (#172B4D), Teal (#167D70), and clean neutral tones.
"""

NAVY = "#172B4D"
TEAL = "#167D70"
LIGHT_BG = "#F7F9FC"
BORDER_COLOR = "#E2E8F0"
TEXT_MUTED = "#64748B"

GLOBAL_CSS = """
<style>
/* ============================================================
   FORCE LIGHT MODE GLOBALLY — sidebar + main content
   ============================================================ */
html, body,
[data-testid="stApp"],
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div,
[data-testid="stSidebarContent"],
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div:first-child {
    background-color: #F8FAFC !important;
    color: #1E293B !important;
}

/* ============================================================
   BASE APP
   ============================================================ */
.stApp {
    background-color: #F8FAFC;
    color: #1E293B;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* ============================================================
   SIDEBAR — full light mode override
   ============================================================ */
[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #E2E8F0 !important;
}

[data-testid="stSidebar"] * {
    color: #1E293B !important;
}

[data-testid="stSidebar"] .stMarkdown h3 {
    color: #172B4D !important;
    font-size: 0.85rem !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    margin-top: 0.75rem !important;
    margin-bottom: 0.3rem !important;
}

[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] small {
    color: #64748B !important;
}

[data-testid="stSidebar"] .stAlert,
[data-testid="stSidebar"] [data-testid="stAlert"] {
    background-color: #EFF6FF !important;
    color: #1E40AF !important;
    border-color: #BFDBFE !important;
}

[data-testid="stSidebar"] .stButton > button {
    background-color: #F1F5F9 !important;
    color: #172B4D !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #E2E8F0 !important;
    border-color: #94A3B8 !important;
}

[data-testid="stSidebar"] hr {
    border-color: #E2E8F0 !important;
}

/* Rename first sidebar navigation link from 'app' to 'Home' */
[data-testid="stSidebarNav"] li:first-child a span,
[data-testid="stSidebarNavItems"] li:first-child a span,
[data-testid="stSidebarNavLink"][href="/"] span,
[data-testid="stSidebarNav"] a[href="/"] span {
    font-size: 0 !important;
}
[data-testid="stSidebarNav"] li:first-child a span::before,
[data-testid="stSidebarNavItems"] li:first-child a span::before,
[data-testid="stSidebarNavLink"][href="/"] span::before,
[data-testid="stSidebarNav"] a[href="/"] span::before {
    content: "Home" !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    visibility: visible !important;
}

/* ============================================================
   MAIN CONTENT — text visibility
   ============================================================ */
h1, h2, h3, h4, h5, h6 {
    color: #172B4D !important;
}

.stMarkdown p, .stMarkdown li {
    color: #1E293B;
}

.stCaption, .stCaption p {
    color: #64748B !important;
}

/* Form labels */
.stTextInput label, .stTextArea label, .stSelectbox label,
.stNumberInput label, .stFileUploader label,
.stCheckbox label, .stDateInput label {
    color: #334155 !important;
    font-weight: 500 !important;
}

/* Input fields */
.stTextInput > div > div > input,
.stTextArea > div > textarea {
    background-color: #FFFFFF !important;
    color: #1E293B !important;
    border-color: #CBD5E1 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab"] {
    color: #64748B !important;
}
.stTabs [aria-selected="true"] {
    color: #172B4D !important;
    font-weight: 600 !important;
}

/* Metric cards */
[data-testid="stMetricValue"] {
    color: #172B4D !important;
    font-weight: 700 !important;
}
[data-testid="stMetricLabel"] {
    color: #64748B !important;
}

/* Dataframe */
[data-testid="stDataFrame"] * {
    color: #1E293B !important;
}

/* Expander */
.streamlit-expanderHeader {
    color: #172B4D !important;
    font-weight: 600 !important;
}

/* ============================================================
   HEADER BANNER
   ============================================================ */
.civic-header {
    background: linear-gradient(135deg, #172B4D 0%, #167D70 100%);
    color: white;
    padding: 1.4rem 2rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
.civic-header h1 {
    color: #FFFFFF !important;
    font-size: 1.8rem !important;
    margin: 0 !important;
    font-weight: 700;
    letter-spacing: -0.5px;
}
.civic-header p {
    color: #E2E8F0 !important;
    margin: 0.35rem 0 0 0 !important;
    font-size: 0.95rem;
}

/* ============================================================
   CARDS
   ============================================================ */
.civic-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
}
.civic-card:hover {
    border-color: #CBD5E1;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.07);
}
.civic-card h3, .civic-card h4 {
    color: #172B4D !important;
}
.civic-card p {
    color: #334155 !important;
}

/* ============================================================
   BADGES
   ============================================================ */
.badge-status {
    display: inline-block;
    padding: 0.2rem 0.55rem;
    font-size: 0.72rem;
    font-weight: 600;
    border-radius: 5px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}
.badge-in-progress  { background: #E0F2FE; color: #0369A1; border: 1px solid #BAE6FD; }
.badge-completed    { background: #DCFCE7; color: #15803D; border: 1px solid #BBF7D0; }
.badge-planned      { background: #FEF3C7; color: #B45309; border: 1px solid #FDE68A; }
.badge-delayed      { background: #FEE2E2; color: #B91C1C; border: 1px solid #FECACA; }
.badge-acknowledged { background: #EDE9FE; color: #6D28D9; border: 1px solid #DDD6FE; }
.badge-pending      { background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; }
.badge-resolved     { background: #DCFCE7; color: #15803D; border: 1px solid #BBF7D0; }

.badge-demo {
    background: #F1F5F9;
    color: #475569;
    border: 1px dashed #94A3B8;
    font-size: 0.7rem;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-weight: 700;
}
.badge-official {
    background: #ECFDF5;
    color: #047857;
    border: 1px solid #A7F3D0;
    font-size: 0.7rem;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-weight: 700;
}

/* ============================================================
   PILOT NOTICE
   ============================================================ */
.pilot-notice {
    background: #EFF6FF;
    border-left: 4px solid #3B82F6;
    padding: 0.65rem 1rem;
    border-radius: 0 6px 6px 0;
    margin-bottom: 1.25rem;
    font-size: 0.85rem;
    color: #1E40AF !important;
}
.pilot-notice strong { color: #1E40AF !important; }
.pilot-notice code {
    background: #DBEAFE;
    color: #1D4ED8;
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 0.8rem;
}

/* ============================================================
   SIDEBAR BRANDING BLOCK
   ============================================================ */
.sidebar-brand {
    padding: 0.75rem 0;
    margin-bottom: 0.75rem;
    border-bottom: 2px solid #E2E8F0;
}
.sidebar-brand h2 {
    color: #172B4D !important;
    font-size: 1.2rem !important;
    font-weight: 800;
    margin: 0 !important;
    letter-spacing: -0.3px;
}
.sidebar-brand small {
    color: #64748B !important;
    font-size: 0.78rem !important;
}

/* ============================================================
   SIDEBAR FOOTER
   ============================================================ */
.sidebar-footer {
    margin-top: 1.5rem;
    padding-top: 0.65rem;
    border-top: 1px solid #E2E8F0;
    color: #94A3B8 !important;
    font-size: 0.75rem;
    text-align: center;
    letter-spacing: 0.2px;
}
</style>
"""
