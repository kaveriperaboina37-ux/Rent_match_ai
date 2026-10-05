import json, os, re

AREAS = [
    "Ameerpet", "Bachupally", "Begumpet", "Gachibowli", "Hafeezpet", "Hitech City", "Jubilee Hills", "Kondapur", "KPHB", "Kukatpally", "Madhapur", "Manikonda", "Miyapur", "Moosapet", "Nizampet",
    "Andheri West, Mumbai", "Powai, Mumbai", "Bandra West, Mumbai", "Koramangala, Bengaluru", "Whitefield, Bengaluru", "Indiranagar, Bengaluru", "Rajajinagar, Bengaluru",
    "Salt Lake, Kolkata", "New Town, Kolkata", "Anna Nagar, Chennai", "OMR, Chennai", "Hinjewadi, Pune", "Kharadi, Pune", "Viman Nagar, Pune", "Golf Course Road, Gurugram", "Sector 62, Noida", "Dwarka, New Delhi", "Indirapuram, Ghaziabad", "Gomti Nagar, Lucknow", "Banjara Hills, Hyderabad", "Panampilly Nagar, Kochi", "Thane West, Thane", "Sector 17, Chandigarh", "Vastrapur, Ahmedabad", "Boring Road, Patna", "Vaishali Nagar, Jaipur"
]

CITY_ALIASES = {
    "mumbai": "Mumbai", "bombay": "Mumbai", "bengaluru": "Bengaluru", "bangalore": "Bengaluru",
    "kolkata": "Kolkata", "calcutta": "Kolkata", "chennai": "Chennai", "madras": "Chennai",
    "pune": "Pune", "gurgaon": "Gurugram", "gurugram": "Gurugram", "noida": "Noida", "delhi": "New Delhi",
    "new delhi": "New Delhi", "ghaziabad": "Ghaziabad", "lucknow": "Lucknow", "hyderabad": "Hyderabad",
    "kochi": "Kochi", "cochin": "Kochi", "thane": "Thane", "chandigarh": "Chandigarh", "ahmedabad": "Ahmedabad",
    "patna": "Patna", "jaipur": "Jaipur"
}


AREA_ALIASES = {
    "hi tech city": "Hitech City", "hi-tech city": "Hitech City", "hitechcity": "Hitech City",
    "kphb colony": "KPHB", "kukatpally housing board": "KPHB", "j hills": "Jubilee Hills",
    "andheri": "Andheri West, Mumbai", "powai": "Powai, Mumbai", "bandra": "Bandra West, Mumbai",
    "koramangala": "Koramangala, Bengaluru", "whitefield": "Whitefield, Bengaluru", "indiranagar": "Indiranagar, Bengaluru", "rajajinagar": "Rajajinagar, Bengaluru",
    "salt lake": "Salt Lake, Kolkata", "new town": "New Town, Kolkata", "anna nagar": "Anna Nagar, Chennai", "omr": "OMR, Chennai",
    "hinjewadi": "Hinjewadi, Pune", "kharadi": "Kharadi, Pune", "viman nagar": "Viman Nagar, Pune", "golf course road": "Golf Course Road, Gurugram",
    "sector 62": "Sector 62, Noida", "dwarka": "Dwarka, New Delhi", "indirapuram": "Indirapuram, Ghaziabad", "gomti nagar": "Gomti Nagar, Lucknow",
    "banjara hills": "Banjara Hills, Hyderabad", "panampilly nagar": "Panampilly Nagar, Kochi", "thane west": "Thane West, Thane",
    "sector 17": "Sector 17, Chandigarh", "vastrapur": "Vastrapur, Ahmedabad", "boring road": "Boring Road, Patna", "vaishali nagar": "Vaishali Nagar, Jaipur"
}


def detect_area(text: str):
    normalized = re.sub(r"[^a-z0-9 ]", " ", text.lower())
    for alias, area in AREA_ALIASES.items():
        if re.search(r"\b" + re.escape(alias) + r"\b", normalized):
            return area
    # Exact locality labels first.
    for area in sorted(AREAS, key=len, reverse=True):
        if area.lower() in normalized:
            return area
    # City-level search: return the city group so all supported localities in that city are matched.
    for alias, city in sorted(CITY_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
        if re.search(r"\b" + re.escape(alias) + r"\b", normalized):
            return city
    return None


def location_matches(property_area: str, requested: str) -> bool:
    p = property_area.lower()
    r = requested.lower()
    if p == r:
        return True
    # City-level request matches all localities belonging to that city.
    return r in p or any(p.endswith(", " + city.lower()) for city in CITY_ALIASES.values() if city.lower() == r)



def local_extract(query: str) -> dict:
    text = query.lower().replace(",", " ")
    area = detect_area(text)
    m = re.search(r"(\d+)\s*(?:bhk|bedroom|bed)\b", text)
    bhk = int(m.group(1)) if m else None
    budget = None
    patterns = [
        r"(?:under|below|less than|max(?:imum)?|budget(?: of)?|upto|up to)\s*(?:₹|rs\.?|inr)?\s*([\d,]+)",
        r"(?:₹|rs\.?|inr)\s*([\d,]+)"
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            budget = int(m.group(1).replace(",", ""))
            break
    return {
        "area": area,
        "bhk": bhk,
        "budget": budget,
        "parking": any(x in text for x in ["parking", "car park", "bike parking"]),
        "wifi": any(x in text for x in ["wi-fi", "wifi", "wi fi", "internet"]),
        "furnished": any(x in text for x in ["furnished", "fully furnished", "semi furnished"]),
    }


def gemini_extract(query: str):
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        return None
    try:
        from google import genai
        client = genai.Client(api_key=key)
        prompt = f"""You are the requirement-extraction component of a rental property AI agent.
Extract ONLY requirements explicitly stated by the user. Return valid JSON with exactly:
area (one of {AREAS}, a supported city name, or null), bhk (integer or null), budget (integer INR or null),
parking (boolean), wifi (boolean), furnished (boolean).
Never invent a location or preference.
User request: {query}"""
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", (response.text or "").strip())
        data = json.loads(text)
        area = data.get("area")
        area = str(area).strip() if area else None
        if area and not any(area.lower() == a.lower() for a in AREAS) and area.lower() in CITY_ALIASES:
            area = CITY_ALIASES[area.lower()]
        elif area and not any(area.lower() == a.lower() for a in AREAS) and area not in CITY_ALIASES.values():
            area = detect_area(str(area))
        return {
            "area": area,
            "bhk": int(data["bhk"]) if data.get("bhk") is not None else None,
            "budget": int(data["budget"]) if data.get("budget") is not None else None,
            "parking": bool(data.get("parking", False)),
            "wifi": bool(data.get("wifi", False)),
            "furnished": bool(data.get("furnished", False)),
        }
    except Exception:
        return None


def extract_requirements(query: str):
    return gemini_extract(query) or local_extract(query)


def tool_search_properties(properties):
    return properties


def tool_filter_properties(properties, r):
    out = properties
    if r.get("area"):
        out = [p for p in out if location_matches(p["area"], r["area"])]
    if r.get("budget") is not None:
        out = [p for p in out if p["rent"] <= r["budget"]]
    if r.get("bhk") is not None:
        out = [p for p in out if p["bhk"] == r["bhk"]]
    if r.get("parking"):
        out = [p for p in out if p["parking"]]
    if r.get("wifi"):
        out = [p for p in out if p["wifi"]]
    if r.get("furnished"):
        out = [p for p in out if p["furnished"]]
    return out


def tool_calculate_match(p, r):
    criteria = []
    if r.get("area"): criteria.append((30, location_matches(p["area"], r["area"]), f"Located in {p['area']}"))
    if r.get("budget") is not None: criteria.append((25, p["rent"] <= r["budget"], "Within budget"))
    if r.get("bhk") is not None: criteria.append((20, p["bhk"] == r["bhk"], f"{p['bhk']} BHK matches"))
    if r.get("parking"): criteria.append((10, p["parking"], "Parking available"))
    if r.get("wifi"): criteria.append((10, p["wifi"], "Wi-Fi available"))
    if r.get("furnished"): criteria.append((5, p["furnished"], "Furnished"))
    if not criteria:
        return 50, [("info", "No specific constraints were detected")]
    total = sum(w for w, _, _ in criteria)
    points = sum(w for w, ok, _ in criteria if ok)
    return round(points / total * 100), [("yes" if ok else "no", reason) for _, ok, reason in criteria]


def run_agent(query, properties):
    requirements = extract_requirements(query)
    searched = tool_search_properties(properties)
    candidates = tool_filter_properties(searched, requirements)
    results = []
    for p in candidates:
        score, reasons = tool_calculate_match(p, requirements)
        results.append({**p, "match_score": score, "reasons": reasons})
    results.sort(key=lambda x: (-x["match_score"], x["rent"]))
    return {
        "requirements": requirements,
        "results": results,
        "agent": {
            "name": "RentMatch AI Agent",
            "ai_provider": "Gemini" if os.getenv("GEMINI_API_KEY", "").strip() else "Built-in requirement parser",
            "tools_used": ["extract_requirements", "search_properties", "filter_properties", "calculate_match"],
            "steps": ["Understand natural-language requirements", "Search the property knowledge base", "Apply explicit hard constraints", "Calculate heuristic match score", "Rank and explain eligible properties"]
        }
    }
