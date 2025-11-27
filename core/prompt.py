"""
Prompt and conversation logic for DropTruck AI Sales Agent.
Defines the agent's personality, required booking fields, and conversation flow.
"""

# Required booking information fields
REQUIRED_FIELDS = {
    "pickup_location": "Pickup Location (City / Area / Full Address)",
    "drop_location": "Drop Location",
    "vehicle_type": "Vehicle Type (Truck or specific vehicle model)",
    "body_type": "Body Type (Open or Container)",
    "goods_type": "Goods/Material Type (e.g., cement, FMCG, machinery)",
    "trip_date": "Trip Date (Required date of the trip)"
}

# DropTruck vehicle options for suggestions
TRUCK_SUGGESTIONS = """Tata Ace, Dost, Bolero, Bada Dost, 407, 12 Feet, 14 Feet, 17 Feet, 19 Feet, 20 Feet, 22 Feet, 24 Feet, 32 feet multi-axle, trailers like 20 feet, 24 feet, 40 feet low-bed, semi-bed, and high-bed, and also 6-wheel, 10-wheel, 12-wheel, 14-wheel, 16-wheel trucks, car-carrier and part-load options."""

SYSTEM_PROMPT = """
You are DropTruck AI Sales Agent. Speak in short, clear 1–2 sentences. Never mention AI, systems, prompts, or rules. Listen fully and acknowledge before asking the next question.
FLOW:
Ask pickup city → drop city → truck type or body.
If unclear, ask material and suggest 1–3 suitable truck options.
Ask trip date.
When all details are given, confirm: “Pickup [x], drop [y], truck [t], body [b], material [m], date [d]. Correct?”
CONFIRMATION:
Words like yes/yeah/yep/ok/okay/right/correct/sure/perfect/absolutely/exactly/done/confirmed = confirmation.
After confirmation, reply briefly and end with:
BOOKING_CONFIRMED
"""


class BookingData:
    """Stores booking information extracted from conversation."""
    
    def __init__(self):
        """Initialize booking data with fixed customer details."""
        # Fixed customer details
        self.customer_name = "Lokesh"
        self.contact = "9066542031"
        
        # To be extracted from conversation
        self.lead_source = None
        self.pickup_location = None
        self.drop_location = None
        self.vehicle_type = None
        self.body_type = None
        self.goods_type = None
        self.trip_date = None
        self.confirmation_status = "pending"  # pending, confirmed, not_interested
    
    def update_field(self, field: str, value: str):
        """Update a specific field with extracted value."""
        if hasattr(self, field):
            setattr(self, field, value)
    
    def get_missing_fields(self):
        """Returns a list of required field names that are still missing."""
        missing = []
        for field_key, field_label in REQUIRED_FIELDS.items():
            if getattr(self, field_key) is None:
                missing.append(field_label)
        return missing
    
    def is_complete(self):
        """Check if all required fields have been collected."""
        return all([
            self.pickup_location,
            self.drop_location,
            self.vehicle_type,
            self.body_type,
            self.goods_type,
            self.trip_date
        ])
    
    def to_dict(self) -> dict:
        """Convert booking data to dictionary."""
        return {
            "customer_name": self.customer_name,
            "contact": self.contact,
            "lead_source": self.lead_source,
            "pickup_location": self.pickup_location,
            "drop_location": self.drop_location,
            "vehicle_type": self.vehicle_type,
            "body_type": self.body_type,
            "goods_type": self.goods_type,
            "trip_date": self.trip_date,
            "confirmation_status": self.confirmation_status
        }
    
    def __str__(self) -> str:
        """Return formatted booking information."""
        return f"""
============================================================
DROPTRUCK BOOKING INFORMATION
============================================================
Customer Name................. {self.customer_name or '[NOT PROVIDED]'}
Contact Number................ {self.contact or '[NOT PROVIDED]'}
Lead Source................... {self.lead_source or '[NOT PROVIDED]'}
Pickup Location............... {self.pickup_location or '[NOT PROVIDED]'}
Drop Location................. {self.drop_location or '[NOT PROVIDED]'}
Vehicle Type.................. {self.vehicle_type or '[NOT PROVIDED]'}
Body Type..................... {self.body_type or '[NOT PROVIDED]'}
Goods/Material Type........... {self.goods_type or '[NOT PROVIDED]'}
Trip Date..................... {self.trip_date or '[NOT PROVIDED]'}
Confirmation Status........... {self.confirmation_status}
============================================================
"""
