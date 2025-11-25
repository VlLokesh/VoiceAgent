"""
Prompt and conversation logic for the transport booking voice agent.
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

# System prompt for the booking agent
SYSTEM_PROMPT = """You are a friendly and professional transport booking assistant for a logistics company. Your job is to help customers book transport services by collecting all necessary information.

You MUST collect the following information from every customer:
1. Pickup Location (City / Area / Full Address)
2. Drop Location
3. Vehicle Type (Truck or specific vehicle model)
4. Body Type ("Open" or "Container")
5. Goods/Material Type (e.g., cement, FMCG, machinery)
6. Trip Date (Required date of the trip)

Guidelines for the conversation:
- Be warm, friendly, and professional
- Ask for information naturally, one or two fields at a time
- If the customer provides multiple pieces of information at once, acknowledge all of them
- Always confirm the details before ending the call
- If any information is unclear or missing, politely ask for clarification
- Use natural language - don't sound robotic
- Keep responses concise and conversational

Example conversation flow:
- Greet the customer warmly
- Ask about their transport needs
- Collect missing information naturally
- Confirm all details once collected
- Thank them and let them know the booking is being processed

Remember: You must collect ALL six pieces of information before the booking can be completed.
"""


class BookingData:
    """Stores and manages booking information collected during the conversation."""
    
    def __init__(self):
        self.pickup_location = None
        self.drop_location = None
        self.vehicle_type = None
        self.body_type = None
        self.goods_type = None
        self.trip_date = None
    
    def update_from_text(self, text: str, field: str, value: str):
        """Update a specific field with extracted value."""
        if field == "pickup_location":
            self.pickup_location = value
        elif field == "drop_location":
            self.drop_location = value
        elif field == "vehicle_type":
            self.vehicle_type = value
        elif field == "body_type":
            self.body_type = value
        elif field == "goods_type":
            self.goods_type = value
        elif field == "trip_date":
            self.trip_date = value
    
    def get_missing_fields(self):
        """Returns a list of field names that are still missing."""
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
            "Pickup Location": self.pickup_location,
            "Drop Location": self.drop_location,
            "Vehicle Type": self.vehicle_type,
            "Body Type": self.body_type,
            "Goods/Material Type": self.goods_type,
            "Trip Date": self.trip_date
        }
    
    def __str__(self):
        """String representation for printing after call."""
        lines = [
            "\n" + "="*60,
            "BOOKING INFORMATION COLLECTED",
            "="*60
        ]
        for key, value in self.to_dict().items():
            status = value if value else "[NOT PROVIDED]"
            lines.append(f"{key:.<30} {status}")
        lines.append("="*60 + "\n")
        return "\n".join(lines)
