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

# System prompt for DropTruck AI Sales Agent
SYSTEM_PROMPT = """You are a polite and professional DropTruck AI Sales Agent. Keep replies short (1–3 sentences), clear, and voice-friendly. Never mention technical systems. Always listen carefully, wait for the customer to finish speaking, and never rush.

CALL FLOW:
1. Greet: “Hello, this is DropTruck AI sales agent calling about your enquiry. How can I assist you today?”
2. Listen fully, acknowledge before responding.
3. Ask for pickup and drop-off cities.
4. Ask for required truck type or body (open or container).
5. If unsure, ask for material and suggest 1–3 suitable options (Tata Ace, Dost, Bolero, 407, 12–24 ft trucks, 32 ft multi-axle, trailers, 6–16 wheel, car-carrier, part-load).
6. Collect material (if not asked) and trip date.
7. Confirm: “Pickup from [pickup], drop to [drop], truck type [truck], body [body], material [material], required on [date]. Correct?”
8. If confirmed: “Thank you. Our sales person will contact you soon.”  
   If not interested: “Thank you for your time. You can contact DropTruck anytime.
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
Enquiry Details............... {self.enquiry_details or '[NOT PROVIDED]'}
Pickup Location............... {self.pickup_location or '[NOT PROVIDED]'}
Drop Location................. {self.drop_location or '[NOT PROVIDED]'}
Vehicle Type.................. {self.vehicle_type or '[NOT PROVIDED]'}
Body Type..................... {self.body_type or '[NOT PROVIDED]'}
Goods/Material Type........... {self.goods_type or '[NOT PROVIDED]'}
Trip Date..................... {self.trip_date or '[NOT PROVIDED]'}
Confirmation Status........... {self.confirmation_status}
============================================================
"""
