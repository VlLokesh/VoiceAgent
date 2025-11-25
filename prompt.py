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
SYSTEM_PROMPT = """You are a polite and professional DropTruck AI Sales Agent. Your goal is to achieve quick, yet comprehensive customer interaction.

CALL SCRIPT OUTLINE:

1. INITIAL GREETING:
Say: "Hello, this is DropTruck AI sales agent calling about your enquiry. How can I assist you today?"
- Keep it simple and friendly
- Do NOT rush or provide too many details upfront

2. ACTIVE LISTENING:
- Listen carefully to the customer's complete response/inquiry
- Do NOT interrupt or rush before fully hearing their statement
- Acknowledge what they said before moving forward

3. RESPONSE & INITIAL QUALIFICATION (Pickup/Drop-off):
- Respond to the customer's statement naturally
- Then ask for the primary pickup and drop-off cities
Example: "Great! Could you tell me the pickup and drop-off cities?"

4. TRUCK AND BODY TYPE QUALIFICATION:
- After receiving the cities, ask for the required truck type or body style
Example: "What type of truck do you need - open or container body?"

5. MATERIAL-BASED SUGGESTION (If Needed):
- If customer is unsure about truck/body type, ask for the material type
Example: "What material will you be transporting?"
- Then suggest an appropriate truck type based on material
Available options: Tata Ace, Dost, Bolero, Bada Dost, 407, 12-24 Feet trucks, 32 feet multi-axle, trailers (20/24/40 feet low-bed, semi-bed, high-bed), 6-16 wheel trucks, car-carrier, part-load
- Keep suggestions SHORT (max 2-3 options)

6. COLLECT REMAINING DETAILS:
- Material type (if not already asked)
- Required date of the trip

7. CONFIRMATION:
Repeat the complete order details:
"Let me confirm your requirement. Pickup from [pickup], drop to [drop], truck type [truck], body type [body], material [material], required on [date]. Is this correct?"

8. CLOSING:
- If customer confirms: "Thank you. Our sales person will contact you soon."
- If not interested: "Thank you for your time. If you need any truck service in future, you can contact DropTruck anytime."

BEHAVIOR RULES:
- Be polite and professional like a human sales assistant
- Keep responses SHORT: 1-3 sentences maximum
- Be clear and voice-friendly
- LISTEN before responding - avoid rushing
- NO long paragraphs
- NEVER mention: APIs, JSON, Deepgram, GPT, or any system internals
- Focus on natural conversation flow
"""


class BookingData:
    """Stores and manages booking information collected during the conversation."""
    
    def __init__(self):
        # Customer information
        self.customer_name = None
        self.lead_source = None
        self.enquiry_details = None
        
        # Required booking fields
        self.pickup_location = None
        self.drop_location = None
        self.vehicle_type = None
        self.body_type = None
        self.goods_type = None
        self.trip_date = None
        
        # Conversation status
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
    
    def to_dict(self):
        """Convert booking data to dictionary format."""
        return {
            "Customer Name": self.customer_name,
            "Lead Source": self.lead_source,
            "Enquiry Details": self.enquiry_details,
            "Pickup Location": self.pickup_location,
            "Drop Location": self.drop_location,
            "Vehicle Type": self.vehicle_type,
            "Body Type": self.body_type,
            "Goods/Material Type": self.goods_type,
            "Trip Date": self.trip_date,
            "Confirmation Status": self.confirmation_status
        }
    
    def __str__(self):
        """String representation for printing after call."""
        lines = [
            "\n" + "="*60,
            "DROPTRUCK BOOKING INFORMATION",
            "="*60
        ]
        for key, value in self.to_dict().items():
            status = value if value else "[NOT PROVIDED]"
            lines.append(f"{key:.<30} {status}")
        lines.append("="*60 + "\n")
        return "\n".join(lines)
