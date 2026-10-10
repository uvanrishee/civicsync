"""
geo_utils.py — Pure-Python geo helpers. No external dependencies.
"""
import math
from typing import List, Dict, Any, Tuple, Optional


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Returns great-circle distance in kilometres between two WGS-84 coordinates.
    Uses the Haversine formula.
    """
    R = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def filter_nearby(
    items: List[Dict[str, Any]],
    home_lat: float,
    home_lon: float,
    radius_km: float = 5.0,
    lat_key: str = "latitude",
    lon_key: str = "longitude"
) -> List[Tuple[Dict[str, Any], float]]:
    """
    Returns a list of (item, distance_km) tuples for all items within radius_km
    of the given home location. Items without valid coordinates are skipped.
    Result is sorted by distance ascending.
    """
    results = []
    for item in items:
        lat = item.get(lat_key)
        lon = item.get(lon_key)
        if lat is None or lon is None:
            continue
        try:
            dist = haversine_km(home_lat, home_lon, float(lat), float(lon))
            if dist <= radius_km:
                results.append((item, dist))
        except (TypeError, ValueError):
            continue
    results.sort(key=lambda x: x[1])
    return results


def annotate_with_distance(
    items: List[Dict[str, Any]],
    home_lat: float,
    home_lon: float,
    lat_key: str = "latitude",
    lon_key: str = "longitude"
) -> List[Dict[str, Any]]:
    """
    Returns a copy of each item with a '_distance_km' field added.
    Items without coords get _distance_km = None.
    """
    result = []
    for item in items:
        lat = item.get(lat_key)
        lon = item.get(lon_key)
        enriched = dict(item)
        if lat is not None and lon is not None:
            try:
                enriched["_distance_km"] = haversine_km(home_lat, home_lon, float(lat), float(lon))
            except (TypeError, ValueError):
                enriched["_distance_km"] = None
        else:
            enriched["_distance_km"] = None
        result.append(enriched)
    return result
