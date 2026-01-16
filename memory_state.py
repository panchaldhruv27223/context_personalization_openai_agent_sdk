from dataclasses import dataclass, field
from typing import Any, Dict, List 

@dataclass
class MemoryNote:
    text: str
    last_update_date: str
    keywords: List[str]
    
@dataclass
class TravelState:
    profile: Dict[str, Any] = field(default_factory=dict)
    
    ## long-term memory
    global_memory: Dict[str, Any] = field(default_factory=lambda: {"notes": []})
    
    ## short-term memory (staging for consolidation)
    session_memory: Dict[str, Any] = field(default_factory=lambda: {"notes": []})
    
    # trip history (recent trips from db)
    trip_history: Dict[str, Any] = field(default_factory=lambda: {"trips": []})
    
    # Rendered injection strings (computed per run)
    system_frontmatter: str = ""
    global_memories_md: str = ""
    session_memories_md: str = ""

    # Flag for triggering session injection after context trimming
    inject_session_memories_next_turn: bool = False
    
    
user_state = TravelState(
    profile={
        "global_customer_id": "crm_12345",
        "name": "John Doe",
        "age": "31",
        "home_city": "San Francisco",
        "currency" : "USD",
        "passport_expiry_date": "2029-06-12",
        "loyalty_status": {"airline": "United Gold", "hotel": "Marriott Titanium"},
        "loyalty_ids": {"marriott": "MR998877", "hilton": "HH445566", "hyatt": "HY112233"},
        "seat_preference": "aisle",
        "tone": "concise and friendly",
        "active_visas": ["Schengen", "US"],
        "insurance_coverage_profile": {
            "car_rental": "primary_cdw_included",
            "travel_medical": "covered",
        },
    },
    global_memory={
        "notes": [
            MemoryNote(
                text="For trips shorter than a week, user generally prefers not to check bags.",
                last_update_date="2025-04-05",
                keywords=["baggage", "short_trip"],
            ).__dict__,
            MemoryNote(
                text="User usually prefers aisle seats.",
                last_update_date="2024-06-25",
                keywords=["seat_preference"],
            ).__dict__,
            MemoryNote(
                text="User generally likes central, walkable city-center neighborhoods.",
                last_update_date="2024-02-11",
                keywords=["neighborhood"],
            ).__dict__,
            MemoryNote(
                text="User generally likes to compare options side-by-side",
                last_update_date="2023-02-17",
                keywords=["pricing"],
            ).__dict__,
            MemoryNote(
                text="User prefers high floors",
                last_update_date="2023-02-11",
                keywords=["room"],
            ).__dict__,
        ]
    },
    trip_history={
        "trips": [
            {
                # Core trip details
                "from_city": "Istanbul",
                "from_country": "Turkey",
                "to_city": "Paris",
                "to_country": "France",
                "check_in_date": "2025-05-01",
                "check_out_date": "2025-05-03",
                "trip_purpose": "leisure",  # leisure | business | family | etc.
                "party_size": 1,

                # Flight details
                "flight": {
                    "airline": "United",
                    "airline_status_at_booking": "United Gold",
                    "cabin_class": "economy_plus",
                    "seat_selected": "aisle",
                    "seat_location": "front",          # front | middle | back
                    "layovers": 1,
                    "baggage": {"checked_bags": 0, "carry_ons": 1},
                    "special_requests": ["vegetarian_meal"],  # optional
                },

                # Hotel details
                "hotel": {
                    "brand": "Hilton",
                    "property_name": "Hilton Paris Opera",
                    "neighborhood": "city_center",
                    "bed_type": "king",
                    "smoking": "non_smoking",
                    "high_floor": True,
                    "early_check_in": False,
                    "late_check_out": True,
                },
            }
        ]
    },
)


# if __name__ == "__main__":
#     mn = MemoryNote(
#                 text="For trips shorter than a week, user generally prefers not to check bags.",
#                 last_update_date="2025-04-05",
#                 keywords=["baggage", "short_trip"],
#             )
    
#     print(mn)
#     print(type(mn))
#     print(type(mn.__dict__))
#     print(mn.__dict__)