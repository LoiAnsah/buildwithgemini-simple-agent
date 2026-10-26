# ruff: noqa
import datetime
from google.cloud import firestore

# IMPORTANT: Hardcoded Project ID string
PROJECT_ID = "qwiklabs-gcp-04-daff5caa8f23"

def seed_database():
    print(f"Connecting to Firestore for project '{PROJECT_ID}'...")
    db = firestore.Client(project=PROJECT_ID)

    # 1. Collection: outing_itineraries
    itineraries = [
        {
            "id": "itin-toronto-fall-2026",
            "title": "Toronto Autumn Wellness & Queen West Flow",
            "date": "2026-10-31",
            "city": "Toronto, ON",
            "participants": ["amalois2003@gmail.com", "loiscodes@gmail.com"],
            "status": "confirmed",
            "weather": {
                "condition": "Crisp Autumn Sun",
                "temperature": "13.5°C (56°F)",
                "wind": "12 km/h Lake Breeze"
            },
            "stops": [
                {
                    "step": 1,
                    "role": "Morning Activity",
                    "time": "10:00 AM",
                    "venue": "Sweat and Tonic",
                    "address": "225 Yonge St / The Well, Toronto, ON",
                    "category": "Pilates & Movement",
                    "neighborhood": "The Well / Spadina",
                    "coordinates": {"lat": 43.6436, "lng": -79.3949},
                    "link": "https://www.sweatandtonic.com"
                },
                {
                    "step": 2,
                    "role": "Healthy Lunch",
                    "time": "11:45 AM",
                    "venue": "Impact Kitchen",
                    "address": "573 King St W, Toronto, ON",
                    "category": "Dining / Healthy",
                    "neighborhood": "King West",
                    "coordinates": {"lat": 43.6449, "lng": -79.4005},
                    "link": "https://www.impactkitchen.ca"
                },
                {
                    "step": 3,
                    "role": "Afternoon Stroll",
                    "time": "1:30 PM",
                    "venue": "Queen West Indie Galleries & Trinity Bellwoods",
                    "address": "Queen St W, Toronto, ON",
                    "category": "Culture & Strolls",
                    "neighborhood": "Queen West",
                    "coordinates": {"lat": 43.6473, "lng": -79.4128},
                    "link": "https://queenwest.org"
                },
                {
                    "step": 4,
                    "role": "Cozy Dinner",
                    "time": "6:00 PM",
                    "venue": "Terroni Queen West",
                    "address": "720 Queen St W, Toronto, ON",
                    "category": "Dining / Italian",
                    "neighborhood": "Queen West",
                    "coordinates": {"lat": 43.6465, "lng": -79.4082},
                    "link": "https://www.terroni.com"
                }
            ],
            "created_at": firestore.SERVER_TIMESTAMP,
            "notes": "Athletic reformer class booked; casual walk through Bellwoods in the afternoon."
        },
        {
            "id": "itin-toronto-nov-pottery",
            "title": "Yorkville Ceramics & French Bistro Outing",
            "date": "2026-11-07",
            "city": "Toronto, ON",
            "participants": ["amalois2003@gmail.com", "loiscodes@gmail.com"],
            "status": "planned",
            "weather": {
                "condition": "Mild Fall Afternoon",
                "temperature": "11°C (52°F)",
                "wind": "8 km/h"
            },
            "stops": [
                {
                    "step": 1,
                    "role": "Morning Pottery Class",
                    "time": "1:00 PM",
                    "venue": "Gardiner Museum Clay Studios",
                    "address": "111 Queen's Park, Toronto, ON",
                    "category": "Pottery & Crafts",
                    "neighborhood": "Yorkville",
                    "coordinates": {"lat": 43.6681, "lng": -79.3927},
                    "link": "https://www.gardinermuseum.on.ca/clay-studios"
                },
                {
                    "step": 2,
                    "role": "Afternoon Tea / Bistro",
                    "time": "3:30 PM",
                    "venue": "Sassafraz",
                    "address": "100 Cumberland St, Toronto, ON",
                    "category": "Dining / French",
                    "neighborhood": "Yorkville",
                    "coordinates": {"lat": 43.6702, "lng": -79.3908},
                    "link": "https://www.sassafraz.ca"
                }
            ],
            "created_at": firestore.SERVER_TIMESTAMP,
            "notes": "Wheel throwing workshop with pottery glazing and warm drinks."
        }
    ]

    for itin in itineraries:
        doc_ref = db.collection("outing_itineraries").document(itin["id"])
        doc_ref.set(itin)
        print(f"Seeded outing_itineraries/{itin['id']} -> {itin['title']}")

    # 2. Collection: user_outing_preferences
    preferences = [
        {
            "email": "amalois2003@gmail.com",
            "home_neighborhood": "Downtown Toronto",
            "favorite_categories": ["Pilates & Movement", "Pottery & Crafts", "Nature & Trails"],
            "preferred_vibes": ["energizing", "tactile", "crisp outdoor"],
            "dietary_notes": "Gluten-free / wholesome cafes like Impact Kitchen",
            "updated_at": firestore.SERVER_TIMESTAMP
        },
        {
            "email": "loiscodes@gmail.com",
            "home_neighborhood": "Toronto (West End)",
            "favorite_categories": ["Rock Climbing", "Reading & Cafes", "Shows & Comedy"],
            "preferred_vibes": ["bouldering", "cozy book salon", "standup comedy"],
            "dietary_notes": "Loves hearty ramen and good local espresso",
            "updated_at": firestore.SERVER_TIMESTAMP
        }
    ]

    for pref in preferences:
        doc_ref = db.collection("user_outing_preferences").document(pref["email"])
        doc_ref.set(pref)
        print(f"Seeded user_outing_preferences/{pref['email']}")

    print("\n✅ Firestore backend seeded successfully!")

if __name__ == "__main__":
    seed_database()
