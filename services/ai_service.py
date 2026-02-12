# This file will later connect to real ML / LLM models

import requests
import re


ISSUE_TAXONOMY = {

    "waste": {
        "open dumping": [
            "garbage", "dump", "trash", "waste on road", "plastic waste"
        ],
        "overflowing bins": [
            "bin full", "dustbin full", "overflowing bin"
        ],
        "illegal dumping": [
            "illegal dumping", "thrown here", "dumped here"
        ],
        "construction debris": [
            "construction waste", "debris", "malba", "rubble"
        ],
        "no waste collection": [
            "no collection", "not collected", "garbage not picked"
        ]
    },

    "water": {
        "water leakage": [
            "leak", "leaking", "water", "pipe burst", "water flowing"
        ],
        "sewage overflow": [
            "sewage", "gutter overflow", "sewer", "drain overflow", "dirty water"
        ],
        "no water supply": [
            "no water", "water not coming", "no supply"
        ],
        "contaminated water": [
            "dirty water", "bad smell water", "contaminated"
        ]
    },

    "air": {
        "open burning": [
            "burning", "burnt", "fire in garbage", "burn waste"
        ],
        "heavy smoke": [
            "smoke", "smog", "pollution", "bad air", "air"
        ],
        "industrial emission": [
            "factory smoke", "chimney", "industrial pollution"
        ]
    },

    "transport": {
        "traffic congestion": [
            "traffic", "jam", "long queue", "truck", "vehicle jam"
        ],
        "broken traffic light": [
            "signal not working", "traffic light broken"
        ],
        "illegal parking": [
            "illegal parking", "wrong parking"
        ],
        "unsafe crossing": [
            "no zebra crossing", "dangerous crossing"
        ]
    },

    "roads": {
        "potholes": [
            "pothole", "road broken", "bad road"
        ],
        "water logging": [
            "water on road", "flooded road", "waterlogging"
        ],
        "open manhole": [
            "manhole open", "open sewer", "open drain"
        ]
    },

    "public infrastructure": {
        "street light not working": [
            "street light", "light not working", "dark road"
        ],
        "damaged footpath": [
            "broken footpath", "footpath damaged"
        ],
        "damaged public property": [
            "broken bench", "damaged park", "broken railing"
        ]
    },

    "greenery": {
        "fallen tree": [
            "tree fallen", "tree fell"
        ],
        "tree cutting": [
            "tree cutting", "trees being cut"
        ],
        "no green cover": [
            "no trees", "no greenery", "barren"
        ]
    },

    "animals": {
        "dead animal": [
            "dead dog", "dead animal", "animal body"
        ],
        "stray animal issue": [
            "stray dogs", "stray cattle", "monkeys problem", "hunt"
        ]
    },

    "noise": {
        "loudspeaker noise": [
            "loudspeaker", "dj", "music", "noise"
        ],
        "construction noise": [
            "construction noise", "drilling", "hammering"
        ]
    },

    "other": {
        "general issue": []
    }
}


# Keep everything lowercase here
DELHI_LOCALITIES = [

    # Central / New Delhi
    "connaught place", "barakhamba road", "mandi house", "ito",
    "pragati maidan", "india gate", "rajpath", "kartavya path",
    "daryaganj", "paharganj", "sadar bazaar", "karol bagh",

    # North Delhi
    "civil lines", "model town", "mukherjee nagar", "gtb nagar",
    "kamla nagar", "burari", "alipur", "narela", "bawana",
    "jahangirpuri", "adarsh nagar", "azadpur", "haiderpur",

    # North West
    "rohini", "pitampura", "shalimar bagh", "ashok vihar",
    "keshav puram", "tri nagar", "rani bagh",

    # West Delhi
    "punjabi bagh", "rajouri garden", "kirti nagar",
    "patel nagar", "moti nagar", "janakpuri",
    "tilak nagar", "vikaspuri", "uttam nagar",
    "paschim vihar", "nangloi", "mundka",

    # South West
    "dwarka", "palam", "najafgarh", "kapashera",
    "mahipalpur", "bijwasan",

    # South Delhi
    "hauz khas", "green park", "sarojini nagar",
    "defence colony", "lajpat nagar", "kalkaji",
    "greater kailash", "malviya nagar", "saket",
    "mehrauli", "chhatarpur", "vasant kunj",
    "vasant vihar", "munirka", "rk puram",

    # South East
    "nehru place", "govindpuri", "okhla",
    "jamia nagar", "jasola", "sarita vihar",

    # East
    "laxmi nagar", "preet vihar", "patparganj",
    "mayur vihar", "vasundhara enclave",
    "geeta colony", "gandhi nagar",

    # North East / Shahdara
    "shahdara", "vivek vihar", "dilshad garden",
    "krishna nagar", "karkardooma",
    "seelampur", "yamuna vihar", "gokalpuri",

    # Popular hubs
    "chandni chowk", "kashmere gate", "anand vihar",
    "sarojini nagar market", "lajpat nagar market",
    "karol bagh market"
]


# ----------------------------------------------------
# Location extraction from text
# ----------------------------------------------------

# ---------------------------------------------------------
# Simple rule based ETA + process predictor (demo version)
# ---------------------------------------------------------

FIX_TIME_RULES = {
    ("waste", "open dumping"): (2, 5),
    ("waste", "overflowing bins"): (1, 2),
    ("waste", "illegal dumping"): (3, 7),
    ("water", "water leakage"): (2, 4),
    ("water", "sewage overflow"): (3, 6),
    ("roads", "potholes"): (5, 10),
    ("roads", "open manhole"): (1, 2),
    ("air", "open burning"): (1, 2),
    ("public infrastructure", "street light not working"): (2, 4),
    ("greenery", "fallen tree"): (1, 3)
}


PROCESS_TEMPLATES = {
    "waste": [
        "Inspection by sanitation supervisor",
        "Verification of complaint location",
        "Deployment of cleaning vehicle and crew",
        "Waste removal and site cleaning",
        "Final inspection and closure"
    ],
    "water": [
        "Inspection by water department team",
        "Leak / blockage identification",
        "Repair work approval",
        "Repair execution",
        "Flow and safety verification"
    ],
    "roads": [
        "Site inspection by engineering team",
        "Damage assessment",
        "Work order generation",
        "Repair and resurfacing",
        "Safety inspection"
    ],
    "air": [
        "Source identification",
        "On-site inspection",
        "Immediate enforcement action",
        "Monitoring for re-occurrence"
    ],
    "public infrastructure": [
        "Department inspection",
        "Maintenance scheduling",
        "Repair / replacement",
        "Functional verification"
    ],
    "greenery": [
        "Site inspection by horticulture team",
        "Risk assessment",
        "Removal / planting activity",
        "Area clean-up",
        "Final verification"
    ]
}


def predict_resolution_time_and_process(category, subcategory):

    key = (category.lower(), subcategory.lower())

    if key in FIX_TIME_RULES:
        low, high = FIX_TIME_RULES[key]
    else:
        low, high = (3, 7)

    process = PROCESS_TEMPLATES.get(
        category.lower(),
        [
            "Department inspection",
            "Work allocation",
            "Execution",
            "Verification",
            "Closure"
        ]
    )

    return {
        "estimated_days_min": low,
        "estimated_days_max": high,
        "process": process
    }


def extract_location_from_text(text):

    if not text:
        return None

    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    found = []

    for place in DELHI_LOCALITIES:
        pattern = r"\b" + re.escape(place) + r"\b"
        if re.search(pattern, text):
            found.append(place)

    if not found:
        return None

    best = max(found, key=len)

    return best.title()


# ----------------------------------------------------
# Reverse geocoding
# ----------------------------------------------------

def reverse_geocode(lat, lng):

    try:
        url = "https://nominatim.openstreetmap.org/reverse"

        params = {
            "format": "jsonv2",
            "lat": lat,
            "lon": lng
        }

        headers = {
            "User-Agent": "civic-sustainability-app"
        }

        res = requests.get(url, params=params, headers=headers, timeout=5)
        data = res.json()

        address = data.get("address", {})

        locality = (
            address.get("suburb")
            or address.get("neighbourhood")
            or address.get("city_district")
            or address.get("city")
        )

        return locality

    except Exception:
        return None


# ----------------------------------------------------
# Improved automatic issue classification
# ----------------------------------------------------

def classify_issue(text):

    if not text or not text.strip():
        return {"category": "other", "subcategory": "general issue"}

    text = text.lower()

    best_score = 0
    best_category = "other"
    best_subcategory = "general issue"

    for category, subs in ISSUE_TAXONOMY.items():
        for subcategory, keywords in subs.items():

            score = 0

            for kw in keywords:
                if kw.lower() in text:
                    score += 1

            if score > best_score:
                best_score = score
                best_category = category
                best_subcategory = subcategory

    return {
        "category": best_category,
        "subcategory": best_subcategory
    }


# ----------------------------------------------------
# Risk estimation placeholder
# ----------------------------------------------------

def predict_risk(classification, location):

    return {
        "severity": "medium",
        "risk_score": 0.62
    }


# ----------------------------------------------------
# Complaint rewrite
# ----------------------------------------------------

def ai_rewrite_complaint(text, category):

    templates = {
        "waste": "This complaint relates to improper solid waste management and public sanitation.",
        "water": "This complaint relates to drinking water supply and sewerage infrastructure.",
        "air": "This complaint relates to air pollution and public health risk.",
        "roads": "This complaint relates to road safety and public infrastructure damage.",
        "public infrastructure": "This complaint relates to malfunctioning public infrastructure.",
        "greenery": "This complaint relates to protection and maintenance of urban green cover.",
        "transport": "This complaint relates to traffic management and road safety.",
    }

    context = templates.get(category.lower(), "This complaint relates to a civic and environmental issue.")

    return (
        f"Respected Sir / Madam,\n\n"
        f"{context}\n\n"
        f"I would like to formally bring the following issue to your notice:\n\n"
        f"{text}\n\n"
        f"This issue is causing inconvenience to residents and may pose environmental and public safety risks. "
        f"I request the concerned department to kindly inspect the location and initiate corrective action at the earliest.\n\n"
        f"Thank you for your attention and support.\n"
        f"Yours sincerely,\n"
        f"A concerned citizen"
    )

from langdetect import detect
from googletrans import Translator

translator = Translator()

def detect_language(text):
    try:
        return detect(text)
    except Exception:
        return "unknown"


def translate_to_english(text):
    try:
        result = translator.translate(text, dest="en")
        return result.text
    except Exception:
        return text
