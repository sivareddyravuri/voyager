"""
Voyager — Travel Data Engine
Generates realistic transport options, hotel data, and attraction listings
"""
import random
from datetime import datetime

# ── Transport ──────────────────────────────────────────────────────────────

TRANSPORT = {
    "Bus": {
        "icon": "🚌",
        "providers": ["RedBus Travels","VRL Travels","SRS Travels","Orange Travels","Kallada Travels","KSRTC Volvo"],
        "features": ["AC Sleeper","USB Charging","Blanket & Pillow","GPS Tracked","Movie Screen","Pushback Seats"],
        "per_km": 0.45, "kmh": 62,
    },
    "Train": {
        "icon": "🚂",
        "providers": ["Rajdhani Express","Shatabdi Express","Vande Bharat","Duronto Express","Garib Rath","Superfast Exp."],
        "features": ["2AC/3AC Berth","Pantry Car","Charging Points","IRCTC eMeal","Bedroll Included","Wi-Fi Zone"],
        "per_km": 0.68, "kmh": 88,
    },
    "Cab": {
        "icon": "🚕",
        "providers": ["Ola Outstation","Uber Intercity","Savaari","DriveU","Meru","Zoomcar Self-Drive"],
        "features": ["Private Ride","Door-to-Door","AC Sedan/SUV","No Stops","Toll Included","24/7 Support"],
        "per_km": 2.90, "kmh": 72,
    },
    "Flight": {
        "icon": "✈️",
        "providers": ["IndiGo","Air India","SpiceJet","Vistara","GoFirst","Akasa Air"],
        "features": ["Check-in 15 kg","Cabin Bag 7 kg","In-flight Snacks","Web Check-in","Free Cancellation","Priority Board"],
        "per_km": 4.50, "kmh": 820,
    },
}

HOTELS = [
    {"name":"The Grand Residency","stars":5,"emoji":"🏨","bg":"linear-gradient(135deg,#e8f4ff,#d0e8ff)",
     "review":"Exceptional service, stunning views and world-class amenities throughout.",
     "rating":4.8,"reviews":"1,240","tag":"Pool & Spa","price":8500,"badge":"Top Rated"},
    {"name":"Serenity Beach Resort","stars":5,"emoji":"🌴","bg":"linear-gradient(135deg,#f0ffe8,#dcfce7)",
     "review":"Beachfront bliss with outstanding breakfast and a breathtaking infinity pool.",
     "rating":4.9,"reviews":"986","tag":"Beachfront","price":12000,"badge":"Guest Favourite"},
    {"name":"Heritage Palace Stays","stars":4,"emoji":"🏰","bg":"linear-gradient(135deg,#f5e8ff,#ede0ff)",
     "review":"Authentic royal architecture, guided heritage tours and home-cooked meals.",
     "rating":4.6,"reviews":"712","tag":"Heritage","price":5800,"badge":"Unique Stay"},
    {"name":"Skyline Boutique Hotel","stars":4,"emoji":"🌇","bg":"linear-gradient(135deg,#fff4e8,#ffe0c0)",
     "review":"Chic rooftop bar with panoramic views. Perfect for business or leisure.",
     "rating":4.5,"reviews":"630","tag":"Rooftop Bar","price":6200,"badge":"Trendy"},
    {"name":"Comfort Inn Express","stars":3,"emoji":"🏩","bg":"linear-gradient(135deg,#fff8e8,#fef3c7)",
     "review":"Spotlessly clean, central location, free breakfast. Great value for money.",
     "rating":4.2,"reviews":"3,100","tag":"Budget Friendly","price":2200,"badge":"Best Value"},
    {"name":"Sunset View Villas","stars":4,"emoji":"🌅","bg":"linear-gradient(135deg,#ffe8e8,#fecaca)",
     "review":"Private pool villas with sea views. Ideal for couples and honeymooners.",
     "rating":4.7,"reviews":"543","tag":"Sea View","price":7000,"badge":"Romantic"},
    {"name":"Eco Stay Boutique","stars":4,"emoji":"🌿","bg":"linear-gradient(135deg,#e8fff5,#d0fae5)",
     "review":"Eco-certified treehouse cottages with organic meals and jungle treks.",
     "rating":4.5,"reviews":"870","tag":"Eco-Certified","price":3400,"badge":"Sustainable"},
    {"name":"City Center Suites","stars":4,"emoji":"🏙️","bg":"linear-gradient(135deg,#e8f0ff,#c8d8ff)",
     "review":"Walking distance to major attractions. Suite rooms with premium amenities.",
     "rating":4.3,"reviews":"1,540","tag":"Prime Location","price":4800,"badge":"Central"},
]

ATTRACTIONS = [
    {"name":"Calangute Beach","icon":"🏖️","type":"Beach",
     "meta":"2.1 km away · 6:00 AM – 10:00 PM · ⭐ 4.6 (18k reviews)","open_from":6,"open_to":22,"fee":0},
    {"name":"Basilica of Bom Jesus","icon":"⛪","type":"Heritage",
     "meta":"4.5 km · 9:00 AM – 6:30 PM · ⭐ 4.8 (9k reviews)","open_from":9,"open_to":18,"fee":0},
    {"name":"Bondla Wildlife Sanctuary","icon":"🦁","type":"Nature",
     "meta":"14 km · 9:30 AM – 5:00 PM · ⭐ 4.3 (2.4k reviews)","open_from":9,"open_to":17,"fee":100},
    {"name":"Fort Aguada","icon":"🏰","type":"Historical",
     "meta":"7.8 km · 9:30 AM – 6:00 PM · ⭐ 4.5 (12k reviews)","open_from":9,"open_to":18,"fee":50},
    {"name":"Mandovi River Cruise","icon":"🛶","type":"Experience",
     "meta":"3.2 km · 6:00 PM – 7:00 PM (Evening) · ⭐ 4.4 (5.2k reviews)","open_from":18,"open_to":19,"fee":350},
    {"name":"Saturday Night Market","icon":"🎨","type":"Market",
     "meta":"6 km · Sat only 6:00 PM – 12:00 AM · ⭐ 4.7 (8k reviews)","open_from":18,"open_to":24,"fee":0},
    {"name":"Dudhsagar Waterfalls","icon":"💧","type":"Nature",
     "meta":"60 km · 6:00 AM – 5:00 PM · ⭐ 4.7 (14k reviews)","open_from":6,"open_to":17,"fee":200},
    {"name":"Old Goa Heritage Walk","icon":"🚶","type":"Tour",
     "meta":"5 km · 8:00 AM – 12:00 PM · ⭐ 4.8 (3.2k reviews)","open_from":8,"open_to":12,"fee":300},
]


def _dist(origin: str, dest: str) -> int:
    seed = abs(hash(origin.lower() + "|" + dest.lower())) % 10000
    rng = random.Random(seed)
    return rng.randint(180, 1800)


def _fmt_dur(hours: float) -> str:
    h = int(hours)
    m = int((hours - h) * 60 // 10) * 10
    return f"{h}h {m:02d}m"


def transport_options(origin: str, dest: str, passengers: int = 1) -> list:
    dist = _dist(origin, dest)
    rng = random.Random(abs(hash(origin + dest)))
    options = []
    for mode, t in TRANSPORT.items():
        base = dist * t["per_km"]
        price = int(base * rng.uniform(0.88, 1.22)) * passengers
        hours = (dist / t["kmh"]) * rng.uniform(1.05, 1.28)
        options.append({
            "mode": mode,
            "icon": t["icon"],
            "provider": rng.choice(t["providers"]),
            "price": price,
            "price_fmt": f"₹{price:,}",
            "duration": _fmt_dur(hours),
            "features": ", ".join(rng.sample(t["features"], 4)),
            "cheapest": False,
        })
    min_p = min(o["price"] for o in options)
    for o in options:
        o["cheapest"] = (o["price"] == min_p)
    return options


def hotels_for(destination: str, budget_max: int = None, stars_min: int = None) -> list:
    rng = random.Random(abs(hash(destination.lower())))
    result = []
    for h in HOTELS:
        p = int(h["price"] * rng.uniform(0.92, 1.14))
        if budget_max and p > budget_max:
            continue
        if stars_min and h["stars"] < stars_min:
            continue
        result.append({**h, "price_fmt": f"₹{p:,}", "price_num": p})
    return result


def attractions_for(destination: str) -> list:
    hour = datetime.now().hour
    result = []
    for a in ATTRACTIONS:
        is_open = a["open_from"] <= hour < a["open_to"]
        result.append({**a, "is_open": is_open,
                       "fee_fmt": f"₹{a['fee']}" if a["fee"] else "Free"})
    return result
