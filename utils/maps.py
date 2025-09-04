import time, math, logging, requests
from typing import Tuple, List, Optional
from .helpers import parse_hungarian_address

logger = logging.getLogger(__name__)

def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    try:
        time.sleep(0.3)
        parsed = parse_hungarian_address(address)
        url = 'https://nominatim.openstreetmap.org/search'
        params = {'q': parsed, 'format': 'json', 'limit': 1, 'countrycodes': 'hu'}
        headers = {'User-Agent': 'OPDBot/1.0'}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            j = r.json()
            if j:
                return float(j[0]['lat']), float(j[0]['lon'])
    except Exception as e:
        logger.error('geocode error: %s', e)
    return None

def haversine_distance(a: Tuple[float,float], b: Tuple[float,float]) -> float:
    lat1, lon1 = a; lat2, lon2 = b
    R = 6371.0
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    aa = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(aa))

def optimize_route(addresses: List[str]) -> List[str]:
    if not addresses:
        return []
    if len(addresses) > 6:
        addresses = addresses[:6]
    coords = []
    valid = []
    for a in addresses:
        g = geocode_address(a)
        if g:
            coords.append(g); valid.append(a)
    if len(valid) <= 1:
        return valid
    optimized = [valid[0]]
    remaining = list(range(1, len(valid)))
    current = coords[0]
    while remaining:
        best = remaining[0]; dist = float('inf')
        for i in remaining:
            d = haversine_distance(current, coords[i])
            if d < dist:
                dist = d; best = i
        optimized.append(valid[best])
        current = coords[best]
        remaining.remove(best)
    return optimized
