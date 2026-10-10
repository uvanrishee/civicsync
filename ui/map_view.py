import folium
from folium.plugins import MarkerCluster
from typing import List, Dict, Any, Optional, Tuple
import streamlit as st
from streamlit_folium import st_folium
from execution.geo_utils import haversine_km

CHENNAI_CENTER = [13.0400, 80.2300]  # Fallback center
PROXIMITY_RADIUS_KM = 5.0

CATEGORY_ICON_CONFIG = {
    "ROADWORKS":      {"color": "blue",      "icon": "road",         "prefix": "fa"},
    "DRAINAGE":       {"color": "darkblue",   "icon": "tint",         "prefix": "fa"},
    "WATER_SEWERAGE": {"color": "cadetblue",  "icon": "wrench",       "prefix": "fa"},
    "ELECTRICAL":     {"color": "orange",     "icon": "bolt",         "prefix": "fa"},
    "METRO_RAIL":     {"color": "purple",     "icon": "subway",       "prefix": "fa"},
    "OTHER":          {"color": "gray",       "icon": "info-circle",  "prefix": "fa"},
}

STATUS_COLORS = {
    "PENDING_REVIEW": ("red",     "exclamation-triangle"),
    "ACKNOWLEDGED":   ("orange",  "eye"),
    "IN_PROGRESS":    ("blue",    "wrench"),
    "RESOLVED":       ("green",   "check-circle"),
    "REJECTED":       ("darkred", "times-circle"),
    "REDIRECTED":     ("gray",    "share"),
}

STATUS_BADGE = {
    "PENDING_REVIEW": ("#FEF3C7", "#B45309", "Pending Review"),
    "ACKNOWLEDGED":   ("#FEF3C7", "#D97706", "Acknowledged"),
    "IN_PROGRESS":    ("#DBEAFE", "#1D4ED8", "In Progress"),
    "RESOLVED":       ("#DCFCE7", "#15803D", "Resolved"),
    "REJECTED":       ("#FEE2E2", "#B91C1C", "Rejected"),
    "REDIRECTED":     ("#F3F4F6", "#374151", "Redirected"),
}


def _dist_label(dist_km: Optional[float]) -> str:
    """Formats a distance float as a short human-readable label."""
    if dist_km is None:
        return ""
    return f" — {dist_km:.1f} km away"


def build_chennai_map(
    projects: List[Dict[str, Any]],
    reports: Optional[List[Dict[str, Any]]] = None,
    show_reports: bool = True,
    home_lat: Optional[float] = None,
    home_lon: Optional[float] = None,
) -> folium.Map:
    """
    Constructs an interactive Folium map.
    - Centers on home_lat/home_lon when provided (citizen proximity mode).
    - Adds a '📍 You are here' star marker at home location.
    - Adds a semi-transparent red circle overlay around active projects within 5 km.
    - Appends distance label to each nearby project tooltip.
    """
    if home_lat is not None and home_lon is not None:
        try:
            home_lat = float(home_lat)
            home_lon = float(home_lon)
            center = [home_lat, home_lon]
            zoom = 14
        except (ValueError, TypeError):
            home_lat = None
            home_lon = None
            center = CHENNAI_CENTER
            zoom = 13
    else:
        center = CHENNAI_CENTER
        zoom = 13

    m = folium.Map(location=center, zoom_start=zoom, tiles="OpenStreetMap", control_scale=True)

    # ── Home pin ──────────────────────────────────────────────────────────────
    if home_lat is not None and home_lon is not None:
        folium.Marker(
            location=[home_lat, home_lon],
            tooltip="📍 Your neighbourhood",
            popup=folium.Popup(
                "<div style='font-family:sans-serif;font-size:13px;'>"
                "<strong>📍 Your saved location</strong><br>"
                f"<small>{home_lat:.4f}, {home_lon:.4f}</small></div>",
                max_width=200
            ),
            icon=folium.Icon(color="black", icon="home", prefix="fa"),
        ).add_to(m)

        # 5 km radius reference ring (light dashed)
        folium.Circle(
            location=[home_lat, home_lon],
            radius=PROXIMITY_RADIUS_KM * 1000,
            color="#6366F1",
            fill=True,
            fill_color="#6366F1",
            fill_opacity=0.04,
            weight=1.5,
            dash_array="6 4",
            tooltip="5 km proximity zone",
        ).add_to(m)

    # ── Public Works markers ──────────────────────────────────────────────────
    for p in projects:
        raw_lat = p.get("latitude")
        raw_lon = p.get("longitude")
        if raw_lat is None or raw_lon is None:
            continue
        try:
            lat = float(raw_lat)
            lon = float(raw_lon)
        except (ValueError, TypeError):
            continue

        cat    = p.get("category", "OTHER")
        config = CATEGORY_ICON_CONFIG.get(cat, CATEGORY_ICON_CONFIG["OTHER"])
        title  = p.get("title", "Public Work")
        org_name = (
            p.get("organizations", {}).get("name")
            if isinstance(p.get("organizations"), dict)
            else "Public Authority"
        )
        status   = p.get("status", "PLANNED")
        end_date = p.get("current_estimated_end_date", "TBD")
        p_id     = p.get("id", "")

        # Compute distance from home if available
        dist_km: Optional[float] = None
        is_nearby = False
        if home_lat is not None and home_lon is not None:
            dist_km = haversine_km(home_lat, home_lon, float(lat), float(lon))
            is_nearby = dist_km <= PROXIMITY_RADIUS_KM

        dist_str = _dist_label(dist_km)

        popup_html = f"""
        <div style="font-family:'Segoe UI',sans-serif; font-size:13px; width:230px; line-height:1.5;">
            <div style="font-size:10px; color:#64748B; font-weight:700; text-transform:uppercase; margin-bottom:3px;">{cat.replace('_',' ')}</div>
            <div style="font-weight:700; color:#172B4D; font-size:14px; margin-bottom:4px;">{title}</div>
            <div style="font-size:12px; margin-bottom:3px;"><strong>Org:</strong> {org_name}</div>
            <div style="font-size:12px; margin-bottom:3px;"><strong>Status:</strong> <span style="background:#E0F2FE;color:#0369A1;padding:2px 6px;border-radius:4px;">{status}</span></div>
            <div style="font-size:12px; margin-bottom:6px;"><strong>Target End:</strong> {end_date}</div>
            {"<div style='font-size:11px;color:#DC2626;font-weight:600;'>📍 " + f"{dist_km:.1f} km from your location</div>" if dist_km is not None else ""}
            <div style="font-size:10px;color:#94A3B8;">ID: {p_id[:8]}…</div>
        </div>
        """

        # Red circle overlay for nearby active projects
        if is_nearby and status in ("IN_PROGRESS", "DELAYED", "PLANNED"):
            folium.Circle(
                location=[lat, lon],
                radius=350,
                color="#DC2626",
                fill=True,
                fill_color="#DC2626",
                fill_opacity=0.18,
                weight=2,
                tooltip=f"⚠️ Active works {dist_km:.1f} km away",
            ).add_to(m)

        folium.Marker(
            location=[lat, lon],
            tooltip=f"{title} ({status}){dist_str}",
            popup=folium.Popup(popup_html, max_width=260),
            icon=folium.Icon(
                color=config["color"],
                icon=config["icon"],
                prefix=config["prefix"]
            ),
        ).add_to(m)

    # ── Citizen Reports markers ───────────────────────────────────────────────
    if show_reports and reports:
        for r in reports:
            raw_lat = r.get("latitude")
            raw_lon = r.get("longitude")
            if raw_lat is None or raw_lon is None:
                continue
            try:
                lat = float(raw_lat)
                lon = float(raw_lon)
            except (ValueError, TypeError):
                continue

            r_id    = r.get("id", "")
            r_cat   = r.get("category", "OTHER").replace("_", " ").title()
            r_status = r.get("status", "PENDING_REVIEW")
            r_loc   = r.get("location_desc") or "Location not specified"
            r_desc  = r.get("description") or ""
            r_desc_short = (r_desc[:100] + "…") if len(r_desc) > 100 else r_desc
            r_date  = str(r.get("created_at", ""))[:10]
            org_obj = r.get("organizations")
            r_org   = org_obj.get("name") if isinstance(org_obj, dict) else "Public Authority"

            # Distance from home
            dist_km = None
            if home_lat is not None and home_lon is not None:
                dist_km = haversine_km(home_lat, home_lon, float(lat), float(lon))

            dist_str = _dist_label(dist_km)

            badge_bg, badge_fg, badge_label = STATUS_BADGE.get(r_status, ("#F3F4F6", "#374151", r_status))
            icon_color, icon_name = STATUS_COLORS.get(r_status, ("red", "exclamation-triangle"))

            rep_popup = f"""
            <div style="font-family:'Segoe UI',sans-serif; font-size:13px; width:240px; line-height:1.5;">
                <div style="font-size:10px;color:#D97706;font-weight:700;letter-spacing:0.5px;margin-bottom:4px;">⚠️ CITIZEN REPORT</div>
                <div style="font-weight:700;color:#172B4D;font-size:14px;margin-bottom:4px;">{r_cat}</div>
                <div style="background:{badge_bg};color:{badge_fg};display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;margin-bottom:6px;">{badge_label}</div>
                <div style="font-size:12px;color:#475569;margin-bottom:4px;">📍 {r_loc}</div>
                <div style="font-size:12px;color:#334155;background:#F8FAFC;padding:6px 8px;border-radius:6px;border:1px solid #E2E8F0;margin-bottom:6px;">{r_desc_short}</div>
                <div style="font-size:11px;color:#64748B;margin-bottom:2px;">🏛️ Assigned to: <strong>{r_org}</strong></div>
                {"<div style='font-size:11px;color:#DC2626;font-weight:600;margin-bottom:2px;'>📍 " + f"{dist_km:.1f} km away</div>" if dist_km is not None else ""}
                <div style="font-size:10px;color:#94A3B8;">📅 Filed: {r_date} &nbsp;|&nbsp; ID: {r_id[:8]}…</div>
            </div>
            """

            folium.Marker(
                location=[lat, lon],
                tooltip=f"⚠️ {r_cat} — {r_status}{dist_str}",
                popup=folium.Popup(rep_popup, max_width=260),
                icon=folium.Icon(color=icon_color, icon=icon_name, prefix="fa"),
            ).add_to(m)

    return m


def render_interactive_map(
    projects: List[Dict[str, Any]],
    reports: Optional[List[Dict[str, Any]]] = None,
    show_reports: bool = True,
    home_lat: Optional[float] = None,
    home_lon: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """Renders map inside Streamlit and listens for click callbacks."""
    m = build_chennai_map(
        projects, reports,
        show_reports=show_reports,
        home_lat=home_lat,
        home_lon=home_lon,
    )
    map_data = st_folium(
        m,
        width="100%",
        height=520,
        returned_objects=["last_object_clicked_popup", "last_clicked"],
    )
    return map_data


def render_pin_drop_map(
    center_lat: float = CHENNAI_CENTER[0],
    center_lon: float = CHENNAI_CENTER[1],
    pinned_lat: Optional[float] = None,
    pinned_lon: Optional[float] = None,
    height: int = 350,
    key: str = "pin_drop_map",
) -> Optional[Dict[str, Any]]:
    """
    Renders an interactive pin-drop map for selecting a neighbourhood location.
    - If pinned_lat and pinned_lon are given, places a prominent draggable red pin at that spot
      along with a 5 km proximity preview ring.
    - Otherwise, places an instructional crosshairs pin at center_lat, center_lon.
    """
    eff_lat = float(pinned_lat) if (pinned_lat is not None) else (float(center_lat) if center_lat is not None else CHENNAI_CENTER[0])
    eff_lon = float(pinned_lon) if (pinned_lon is not None) else (float(center_lon) if center_lon is not None else CHENNAI_CENTER[1])

    m = folium.Map(
        location=[eff_lat, eff_lon],
        zoom_start=14 if (pinned_lat is not None) else 13,
        tiles="OpenStreetMap",
    )

    if pinned_lat is not None and pinned_lon is not None:
        # 5 km proximity preview ring
        folium.Circle(
            location=[eff_lat, eff_lon],
            radius=int(PROXIMITY_RADIUS_KM * 1000),
            color="#DC2626",
            fill=True,
            fill_color="#DC2626",
            fill_opacity=0.08,
            weight=1.5,
            dash_array="6 4",
            tooltip="5 km Proximity Radius",
        ).add_to(m)

        # Prominent red pin at selected spot
        folium.Marker(
            location=[eff_lat, eff_lon],
            tooltip=f"📍 Selected Pin: {eff_lat:.4f}, {eff_lon:.4f} (Click anywhere to move)",
            popup=folium.Popup(
                f"<div style='font-family:sans-serif;font-size:13px;'>"
                f"<strong>📍 Selected Location</strong><br>"
                f"Lat: {eff_lat:.5f}<br>Lon: {eff_lon:.5f}</div>",
                max_width=220
            ),
            icon=folium.Icon(color="red", icon="home", prefix="fa"),
        ).add_to(m)
    else:
        # Default prompt pin
        folium.Marker(
            location=[eff_lat, eff_lon],
            tooltip="Click anywhere on the map to drop your neighbourhood pin",
            icon=folium.Icon(color="blue", icon="crosshairs", prefix="fa"),
        ).add_to(m)

    return st_folium(
        m,
        width="100%",
        height=height,
        returned_objects=["last_clicked"],
        key=key,
    )
