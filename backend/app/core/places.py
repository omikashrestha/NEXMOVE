import math
import os
import urllib.parse
from typing import List, Dict, Any, Optional, Tuple

# Comprehensive directory of major Indian cities, coordinates, and states
INDIAN_CITIES: List[Dict[str, Any]] = [
    {"name": "Bengaluru", "state": "Karnataka", "lat": 12.9716, "lon": 77.5946, "aliases": ["Bangalore"]},
    {"name": "Kolkata", "state": "West Bengal", "lat": 22.5726, "lon": 88.3639, "aliases": ["Calcutta"]},
    {"name": "Pune", "state": "Maharashtra", "lat": 18.5204, "lon": 73.8567, "aliases": []},
    {"name": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lon": 72.8777, "aliases": ["Bombay"]},
    {"name": "Hyderabad", "state": "Telangana", "lat": 17.3850, "lon": 78.4867, "aliases": ["Secunderabad"]},
    {"name": "Delhi", "state": "Delhi NCR", "lat": 28.7041, "lon": 77.1025, "aliases": ["New Delhi", "NCR"]},
    {"name": "Gurugram", "state": "Haryana", "lat": 28.4595, "lon": 77.0266, "aliases": ["Gurgaon"]},
    {"name": "Noida", "state": "Uttar Pradesh", "lat": 28.5355, "lon": 77.3910, "aliases": ["Greater Noida"]},
    {"name": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lon": 80.2707, "aliases": ["Madras"]},
    {"name": "Ahmedabad", "state": "Gujarat", "lat": 23.0225, "lon": 72.5714, "aliases": []},
    {"name": "Patna", "state": "Bihar", "lat": 25.5941, "lon": 85.1376, "aliases": []},
    {"name": "Jaipur", "state": "Rajasthan", "lat": 26.9124, "lon": 75.7873, "aliases": []},
    {"name": "Kochi", "state": "Kerala", "lat": 9.9312, "lon": 76.2673, "aliases": ["Cochin", "Ernakulam"]},
    {"name": "Chandigarh", "state": "Punjab / Haryana", "lat": 30.7333, "lon": 76.7794, "aliases": ["Mohali", "Panchkula"]},
    {"name": "Lucknow", "state": "Uttar Pradesh", "lat": 26.8467, "lon": 80.9462, "aliases": []},
    {"name": "Indore", "state": "Madhya Pradesh", "lat": 22.7196, "lon": 75.8577, "aliases": []},
    {"name": "Bhopal", "state": "Madhya Pradesh", "lat": 23.2599, "lon": 77.4126, "aliases": []},
    {"name": "Nagpur", "state": "Maharashtra", "lat": 21.1458, "lon": 79.0882, "aliases": []},
    {"name": "Coimbatore", "state": "Tamil Nadu", "lat": 11.0168, "lon": 76.9558, "aliases": []},
    {"name": "Visakhapatnam", "state": "Andhra Pradesh", "lat": 17.6868, "lon": 83.2185, "aliases": ["Vizag"]},
    {"name": "Bhubaneswar", "state": "Odisha", "lat": 20.2961, "lon": 85.8245, "aliases": []},
    {"name": "Thiruvananthapuram", "state": "Kerala", "lat": 8.5241, "lon": 76.9366, "aliases": ["Trivandrum"]},
    {"name": "Surat", "state": "Gujarat", "lat": 21.1702, "lon": 72.8311, "aliases": []},
    {"name": "Vadodara", "state": "Gujarat", "lat": 22.3072, "lon": 73.1812, "aliases": ["Baroda"]},
    {"name": "Goa (Panaji)", "state": "Goa", "lat": 15.4909, "lon": 73.8278, "aliases": ["Panjim", "Goa"]},
    {"name": "Guwahati", "state": "Assam", "lat": 26.1445, "lon": 91.7362, "aliases": []},
    {"name": "Ranchi", "state": "Jharkhand", "lat": 23.3441, "lon": 85.3096, "aliases": []},
    {"name": "Dehradun", "state": "Uttarakhand", "lat": 30.3165, "lon": 78.0322, "aliases": []},
    {"name": "Mysuru", "state": "Karnataka", "lat": 12.2958, "lon": 76.6394, "aliases": ["Mysore"]},
    {"name": "Mangaluru", "state": "Karnataka", "lat": 12.9141, "lon": 74.8560, "aliases": ["Mangalore"]}
]

# Major tech parks, SEZs, and business districts mapped by city
CITY_WORKPLACES: Dict[str, List[Dict[str, str]]] = {
    "bengaluru": [
        {"name": "Manyata Tech Park", "area": "Hebbal / Nagavara", "category": "Tech Park"},
        {"name": "Outer Ring Road (Ecospace / Cessna)", "area": "Bellandur / Marathahalli", "category": "IT Corridor"},
        {"name": "Electronic City Phase 1 & 2", "area": "Hosur Road", "category": "Tech Hub"},
        {"name": "International Tech Park Bangalore (ITPB)", "area": "Whitefield", "category": "Tech Park"},
        {"name": "Embassy GolfLinks (EGL)", "area": "Domlur / Indiranagar", "category": "Business Park"},
        {"name": "Bagmane Tech Park", "area": "CV Raman Nagar", "category": "Tech Park"},
        {"name": "Koramangala Commercial Hub", "area": "Koramangala", "category": "Startup District"},
        {"name": "CBD / MG Road / Brigade Road", "area": "Central Bengaluru", "category": "Central Business District"}
    ],
    "kolkata": [
        {"name": "Salt Lake Sector V", "area": "Bidhannagar", "category": "IT & Electronics Hub"},
        {"name": "Rajarhat New Town Financial Hub", "area": "New Town Action Area II", "category": "Financial & Tech Park"},
        {"name": "Ecospace Business Park", "area": "New Town", "category": "Commercial Park"},
        {"name": "DLF IT Park", "area": "Rajarhat", "category": "IT Park"},
        {"name": "Dalhousie / BBD Bagh", "area": "Central Kolkata", "category": "Central Business District"},
        {"name": "Park Street Commercial District", "area": "Central Kolkata", "category": "Commercial Zone"},
        {"name": "Kasba Industrial Estate / Ruby", "area": "EM Bypass", "category": "Commercial Zone"}
    ],
    "pune": [
        {"name": "Hinjawadi Rajiv Gandhi Infotech Park (Ph 1, 2, 3)", "area": "Hinjawadi", "category": "IT Mega Hub"},
        {"name": "Magarpatta Cybercity", "area": "Hadapsar", "category": "Integrated IT City"},
        {"name": "EON Free Zone / Kharadi IT Park", "area": "Kharadi", "category": "IT SEZ"},
        {"name": "Viman Nagar Commercial Area", "area": "Viman Nagar", "category": "Business District"},
        {"name": "Senapati Bapat Road / ICC Towers", "area": "Shivajinagar", "category": "Commercial Center"},
        {"name": "Baner - Balewadi High Street", "area": "Baner", "category": "Corporate Corridor"}
    ],
    "mumbai": [
        {"name": "Bandra Kurla Complex (BKC)", "area": "Bandra East", "category": "Financial & Corporate Center"},
        {"name": "Mindspace & Infinity IT Park", "area": "Malad West", "category": "IT Park"},
        {"name": "Nesco IT Park", "area": "Goregaon East", "category": "IT Park"},
        {"name": "Hiranandani Business Park", "area": "Powai", "category": "Corporate SEZ"},
        {"name": "Lower Parel Commercial Hub (One World Center)", "area": "Lower Parel", "category": "Corporate Corridor"},
        {"name": "Airoli Mindspace & Gigaplex", "area": "Navi Mumbai", "category": "IT SEZ"},
        {"name": "Nariman Point / Fort", "area": "South Mumbai", "category": "Central Business District"}
    ],
    "hyderabad": [
        {"name": "HITEC City (Cyber Towers / Cyber Gateway)", "area": "Madhapur", "category": "IT Corridor"},
        {"name": "Financial District (Nanakramguda)", "area": "Gachibowli", "category": "Banking & IT Hub"},
        {"name": "Mindspace Madhapur", "area": "Madhapur", "category": "IT SEZ"},
        {"name": "Raheja Mindspace IT Park", "area": "Hitec City", "category": "IT Park"},
        {"name": "Begumpet & Somajiguda Commercial Area", "area": "Central Hyderabad", "category": "Business District"}
    ],
    "delhi": [
        {"name": "DLF Cyber City & Cyber Hub", "area": "Gurugram Phase 2", "category": "Corporate Hub"},
        {"name": "Golf Course Road Corporate Corridor", "area": "Gurugram", "category": "Financial Corridor"},
        {"name": "Sector 62 IT Corridor", "area": "Noida", "category": "IT Hub"},
        {"name": "Connaught Place (CP)", "area": "Central Delhi", "category": "Central Business District"},
        {"name": "Okhla Industrial Area Ph 1-3", "area": "South Delhi", "category": "Commercial Hub"},
        {"name": "Barakhamba Road / KG Marg", "area": "Central Delhi", "category": "Financial Center"}
    ],
    "chennai": [
        {"name": "OMR IT Corridor (Tidel Park & Ascendas)", "area": "Tharamani", "category": "IT Expressway"},
        {"name": "DLF Cybercity", "area": "Manapakkam / Porur", "category": "IT SEZ"},
        {"name": "Guindy Industrial & Tech Park", "area": "Guindy", "category": "Industrial / IT Hub"},
        {"name": "Ambattur IT Park", "area": "Ambattur", "category": "Industrial & Tech Park"}
    ],
    "patna": [
        {"name": "Fraser Road Commercial District", "area": "Fraser Road", "category": "Commercial Hub"},
        {"name": "Exhibition Road Corporate Center", "area": "Central Patna", "category": "Business District"},
        {"name": "Patliputra Industrial Area", "area": "Patliputra", "category": "Industrial Zone"},
        {"name": "Dak Bungalow Crossing", "area": "Central Patna", "category": "Commercial Center"}
    ],
    "ahmedabad": [
        {"name": "GIFT City (Gujarat International Finance Tec-City)", "area": "Gandhinagar / Ahmedabad", "category": "Financial SEZ"},
        {"name": "SG Highway Corporate Corridor", "area": "Bodakdev / Thaltej", "category": "Commercial Hub"},
        {"name": "Prahlad Nagar Corporate Road", "area": "Prahlad Nagar", "category": "Business District"},
        {"name": "Ashram Road Financial District", "area": "Navrangpura", "category": "Central Commercial Hub"}
    ],
    "jaipur": [
        {"name": "Mahindra World City SEZ", "area": "Ajmer Road", "category": "IT & Industrial SEZ"},
        {"name": "Sitapura Industrial Area & EPIP", "area": "Sitapura", "category": "IT & Export Zone"},
        {"name": "Malviya Nagar Commercial Area", "area": "Malviya Nagar", "category": "Commercial District"}
    ],
    "kochi": [
        {"name": "Infopark Phase 1 & 2", "area": "Kakkanad", "category": "IT Mega Hub"},
        {"name": "SmartCity Kochi", "area": "Kakkanad", "category": "IT SEZ"},
        {"name": "MG Road Commercial Corridor", "area": "Ernakulam", "category": "Central Commercial District"}
    ]
}


def search_indian_cities(query: str = "") -> List[Dict[str, Any]]:
    """Returns matching Indian cities for searchable autocomplete with fallback."""
    q = (query or "").strip().lower()
    if not q:
        # Return popular major hubs first
        return [c for c in INDIAN_CITIES if c["name"] in ["Bengaluru", "Pune", "Kolkata", "Mumbai", "Hyderabad", "Delhi", "Chennai", "Ahmedabad", "Patna", "Jaipur"]]
    
    matches = []
    for city in INDIAN_CITIES:
        if q in city["name"].lower() or any(q in alias.lower() for alias in city.get("aliases", [])) or q in city["state"].lower():
            matches.append(city)
    return matches


def get_city_coordinates(city_name: str) -> Optional[Tuple[float, float]]:
    """Finds latitude and longitude for a city name."""
    c_lower = (city_name or "").strip().lower()
    for c in INDIAN_CITIES:
        if c["name"].lower() == c_lower or any(alias.lower() == c_lower for alias in c.get("aliases", [])):
            return (c["lat"], c["lon"])
    return None


def calculate_intercity_distance_km(origin_city: str, dest_city: str) -> int:
    """
    Calculates realistic interstate road highway distance in km between any two Indian cities.
    Uses known major highway corridors first, followed by Haversine formula with a realistic
    Indian road tortuosity factor (1.25x).
    """
    o_clean = origin_city.strip().lower()
    d_clean = dest_city.strip().lower()

    if o_clean == d_clean:
        return 35  # Intra-city moving average

    # Direct highway lookup
    corridor_map = {
        ("pune", "kolkata"): 1650,
        ("kolkata", "pune"): 1650,
        ("pune", "bengaluru"): 840,
        ("bengaluru", "pune"): 840,
        ("mumbai", "bengaluru"): 980,
        ("bengaluru", "mumbai"): 980,
        ("hyderabad", "bengaluru"): 570,
        ("bengaluru", "hyderabad"): 570,
        ("delhi", "bengaluru"): 2150,
        ("bengaluru", "delhi"): 2150,
        ("delhi", "kolkata"): 1530,
        ("kolkata", "delhi"): 1530,
        ("mumbai", "kolkata"): 1960,
        ("kolkata", "mumbai"): 1960,
        ("bengaluru", "kolkata"): 1870,
        ("kolkata", "bengaluru"): 1870,
        ("pune", "mumbai"): 150,
        ("mumbai", "pune"): 150,
        ("pune", "hyderabad"): 560,
        ("hyderabad", "pune"): 560,
        ("delhi", "mumbai"): 1420,
        ("mumbai", "delhi"): 1420,
        ("chennai", "bengaluru"): 350,
        ("bengaluru", "chennai"): 350,
        ("patna", "kolkata"): 580,
        ("kolkata", "patna"): 580,
        ("patna", "delhi"): 1050,
        ("delhi", "patna"): 1050,
        ("patna", "pune"): 1680,
        ("pune", "patna"): 1680,
        ("patna", "bengaluru"): 2050,
        ("bengaluru", "patna"): 2050,
        ("ahmedabad", "mumbai"): 530,
        ("mumbai", "ahmedabad"): 530,
        ("ahmedabad", "pune"): 660,
        ("pune", "ahmedabad"): 660,
        ("kochi", "bengaluru"): 550,
        ("bengaluru", "kochi"): 550,
        ("jaipur", "delhi"): 280,
        ("delhi", "jaipur"): 280,
    }

    if (o_clean, d_clean) in corridor_map:
        return corridor_map[(o_clean, d_clean)]

    # Compute via coordinates
    c1 = get_city_coordinates(origin_city)
    c2 = get_city_coordinates(dest_city)

    if c1 and c2:
        lat1, lon1 = c1
        lat2, lon2 = c2
        # Haversine formula
        r = 6371.0  # Earth radius in km
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        aerial_dist = r * c
        # Realistic Indian road distance is ~1.25x straight-line aerial distance
        highway_dist = int(round(aerial_dist * 1.25))
        return max(50, highway_dist)

    # General fallback for unrecognized locations
    return 1100


def search_workplaces(city_name: str, query: str = "") -> List[Dict[str, str]]:
    """
    Returns business districts, IT corridors, tech parks, and commercial hubs for the selected city.
    Uses curated database and allows arbitrary user search filtering.
    """
    c_clean = (city_name or "").strip().lower()
    q_clean = (query or "").strip().lower()

    # Find matching city key
    matched_key = None
    for k in CITY_WORKPLACES:
        if k in c_clean or c_clean in k:
            matched_key = k
            break

    results: List[Dict[str, str]] = []
    if matched_key and matched_key in CITY_WORKPLACES:
        hub_list = CITY_WORKPLACES[matched_key]
        for hub in hub_list:
            if not q_clean or q_clean in hub["name"].lower() or q_clean in hub["area"].lower() or q_clean in hub["category"].lower():
                results.append({
                    "name": hub["name"],
                    "area": hub["area"],
                    "category": hub["category"],
                    "city": city_name
                })

    # If query is non-empty and not in results, include custom manual entry option
    if q_clean and not any(r["name"].lower() == q_clean for r in results):
        results.append({
            "name": query.strip(),
            "area": f"{city_name} (Custom Location)",
            "category": "Manual Entry",
            "city": city_name
        })

    # If city has no pre-curated hubs, provide generic fallback options
    if not results:
        results = [
            {"name": f"{city_name} City Center / CBD", "area": "Central", "category": "Commercial Hub", "city": city_name},
            {"name": f"{city_name} Industrial Area", "area": "Industrial Zone", "category": "Business Park", "city": city_name},
            {"name": f"{city_name} IT & Tech Zone", "area": "Tech Corridor", "category": "Tech Park", "city": city_name}
        ]
        if q_clean:
            results.insert(0, {
                "name": query.strip(),
                "area": f"{city_name} (User Specified)",
                "category": "Manual Entry",
                "city": city_name
            })

    return results
