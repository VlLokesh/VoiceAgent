"""
LLM integration module for the voice agent.
Manages conversation with OpenAI API and extracts booking information.
"""

import os
import requests
from core.prompt import SYSTEM_PROMPT, BookingData


class LLMAgent:
    """Manages LLM interactions and conversation state."""
    
    def __init__(self, api_key: str = None, model: str = None, logger=None):
        """
        Initialize LLM agent.
        
        Args:
            api_key: OpenAI API key (reads from env if not provided)
            model: OpenAI model to use (default: gpt-4o-mini)
            logger: WorkflowLogger instance for logging conversations
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.logger = logger
        
        if not self.api_key:
            print("⚠️  WARNING: OPENAI_API_KEY not set. Agent will use echo mode.")
        
        self.conversation_history = []
        self.booking_data = BookingData()
        
        # Initialize conversation with system prompt
        if self.api_key:
            self.conversation_history.append({
                "role": "system",
                "content": SYSTEM_PROMPT
            })
    
    def generate_response(self, user_text: str) -> str:
        """
        Generate a response to user input.
        
        Args:
            user_text: User's spoken text
            
        Returns:
            Assistant's response text
        """
        if not user_text or not user_text.strip():
            return "I didn't catch that. Could you please repeat?"
        
        # Extract booking information from user text
        self._extract_booking_info(user_text)
        
        # Detect confirmation status
        self._detect_confirmation(user_text)
        
        # If no API key, use echo mode
        if not self.api_key:
            response = f"[Echo Mode] You said: {user_text}"
            if self.logger:
                self.logger.log_conversation_turn(user_text, response)
            return response
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_text
        })
        
        # Keep only recent messages to control token usage
        recent_messages = self._get_recent_messages()
        
        # Call OpenAI API
        try:
            response_text = self._call_openai(recent_messages)
            
            # Extract from LLM response too (captures locations from confirmations)
            self._extract_booking_info(response_text)
            
            # Check if response contains BOOKING_CONFIRMED marker
            if self.check_booking_confirmed_marker(response_text):
                self.booking_data.confirmation_status = "confirmed"
                if self.logger:
                    self.logger.log_confirmation_status("confirmed")
                    self.logger.log_info("BOOKING_CONFIRMED marker detected in LLM response")
            
            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })
            
            # Log conversation turn
            if self.logger:
                self.logger.log_conversation_turn(user_text, response_text)
            
            return response_text
            
        except Exception as e:
            print(f"❌ LLM error: {e}")
            error_response = "I'm having trouble processing that right now. Could you try again?"
            if self.logger:
                self.logger.log_conversation_turn(user_text, error_response)
            return error_response
    
    def is_call_complete(self) -> bool:
        """
        Check if the call should be ended based on assistant's last response.
        Returns True if the assistant has said goodbye or confirmed booking.
        """
        if not self.conversation_history:
            return False
        
        # Get the last assistant message
        last_message = None
        for msg in reversed(self.conversation_history):
            if msg["role"] == "assistant":
                last_message = msg["content"].lower()
                break
        
        if not last_message:
            return False
        
        # Check for BOOKING_CONFIRMED marker (highest priority)
        if "booking_confirmed" in last_message:
            return True
        
        # Check for closing phrases
        closing_phrases = [
            "have a great day",
            "have a good day", 
            "thank you for your time",
            "goodbye",
            "bye",
            "our sales person will contact you soon",
            "you can contact droptruck anytime"
        ]
        
        return any(phrase in last_message for phrase in closing_phrases)
    
    def _call_openai(self, messages: list) -> str:
        """
        Call OpenAI API with conversation messages.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Assistant's response text
        """
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.6,
            "max_tokens": 256
        }
        
        print("🤖 Calling LLM...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"OpenAI API error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            raise Exception(f"OpenAI API returned status {response.status_code}")
        
        data = response.json()
        return data['choices'][0]['message']['content']
    
    def _get_recent_messages(self, max_exchanges: int = 10) -> list:
        """
        Get recent conversation messages to control token usage.
        Args:
            max_exchanges: Maximum number of user-assistant exchanges to keep
        Returns:
            List of recent messages including system prompt
        """
        # Always include system prompt
        system_messages = [msg for msg in self.conversation_history if msg["role"] == "system"]
        
        # Get recent user/assistant messages
        other_messages = [msg for msg in self.conversation_history if msg["role"] != "system"]
        recent_other = other_messages[-(max_exchanges * 2):]
        
        return system_messages + recent_other
    
    def _extract_booking_info(self, text: str):
        """
        Extract booking information from user text using pattern matching.
        This is a simple extraction - the LLM will handle the conversation flow.
        
        Args:
            text: User's spoken text
        """
        text_lower = text.lower()
        
        # Extract pickup and drop locations
        # Pattern: "from X to Y" or "X to Y" or "trip from X to Y"
        import re
        
        # Try to find "from X to Y" pattern (more flexible)
        # Allow updates if user provides clearer information
        from_to_pattern = r'(?:from|pickup|trip from)\s+([a-zA-Z\s]+?)\s+(?:to|drop)\s+([a-zA-Z\s]+?)(?:\s|,|$|\.|\band\b)'
        match = re.search(from_to_pattern, text_lower)
        if match:
            pickup = match.group(1).strip().title()
            drop = match.group(2).strip().title()
            
            # Update if field is empty OR if new value is longer/clearer (likely a correction)
            if not self.booking_data.pickup_location or len(pickup) > len(self.booking_data.pickup_location or ""):
                self.booking_data.pickup_location = pickup
                if self.logger:
                    self.logger.log_booking_update("pickup_location", pickup)
            
            if not self.booking_data.drop_location or len(drop) > len(self.booking_data.drop_location or ""):
                self.booking_data.drop_location = drop
                if self.logger:
                    self.logger.log_booking_update("drop_location", drop)
        
        # Also try confirmation format: "Pickup X, drop Y" or "Pickup in X, drop in Y"
        # Updated regex to handle "in" optionally and capture the city name
        confirmation_pattern = r'pickup\s+(?:in\s+)?([a-zA-Z\s]+?),\s*drop\s+(?:in\s+)?([a-zA-Z\s]+?)(?:,|truck|\s+truck|\.|$)'
        conf_match = re.search(confirmation_pattern, text_lower)
        if conf_match:
            pickup = conf_match.group(1).strip().title()
            drop = conf_match.group(2).strip().title()
            
            # Clean up common prefixes/suffixes (case-insensitive)
            for prefix in ['in ', 'from ', 'at ']:
                if pickup.lower().startswith(prefix):
                    pickup = pickup[len(prefix):].title()
                if drop.lower().startswith(prefix):
                    drop = drop[len(prefix):].title()
            
            # Always update from confirmation (it's the AI's understanding)
            if pickup and len(pickup) > 2:
                self.booking_data.pickup_location = pickup
                if self.logger:
                    self.logger.log_booking_update("pickup_location", pickup)
            
            if drop and len(drop) > 2:
                self.booking_data.drop_location = drop
                if self.logger:
                    self.logger.log_booking_update("drop_location", drop)
        
        # Detect body type
        if "open" in text_lower and self.booking_data.body_type is None:
            self.booking_data.body_type = "Open"
            if self.logger:
                self.logger.log_booking_update("body_type", "Open")
        elif "container" in text_lower and self.booking_data.body_type is None:
            self.booking_data.body_type = "Container"
            if self.logger:
                self.logger.log_booking_update("body_type", "Container")
        
        # Detect vehicle type mentions with fuzzy matching
        # This handles mispronunciations and different accents
        
        # List of all vehicle types to match against
        vehicle_keywords = {
            # Basic trucks
            "tata ace": "Tata Ace",
            "tata ac": "Tata Ace",
            "ace": "Tata Ace",
            "dost": "Dost",
            "bada dost": "Bada Dost",
            "bolero": "Bolero",
            "bolero pickup": "Bolero",
            "407": "407",
            "eicher": "Eicher",
            "ashok leyland": "Ashok Leyland",
            
            # Feet-based trucks
            "12 feet": "12 Feet",
            "14 feet": "14 Feet",
            "17 feet": "17 Feet",
            "19 feet": "19 Feet",
            "20 feet": "20 Feet",
            "22 feet": "22 Feet",
            "24 feet": "24 Feet",
            "32 feet": "32 Feet Multi-Axle",
            "32 feet multi-axle": "32 Feet Multi-Axle",
            "32 feet multi axle": "32 Feet Multi-Axle",
            
            # Trailers
            "trailer": "Trailer",
            "20 feet trailer": "20 Feet Trailer",
            "24 feet trailer": "24 Feet Trailer",
            "40 feet trailer": "40 Feet Trailer",
            "low-bed": "Low-Bed Trailer",
            "low bed": "Low-Bed Trailer",
            "semi-bed": "Semi-Bed Trailer",
            "semi bed": "Semi-Bed Trailer",
            "high-bed": "High-Bed Trailer",
            "high bed": "High-Bed Trailer",
            
            # Wheel configurations
            "6-wheel": "6-Wheel Truck",
            "6 wheel": "6-Wheel Truck",
            "10-wheel": "10-Wheel Truck",
            "10 wheel": "10-Wheel Truck",
            "12-wheel": "12-Wheel Truck",
            "12 wheel": "12-Wheel Truck",
            "14-wheel": "14-Wheel Truck",
            "14 wheel": "14-Wheel Truck",
            "16-wheel": "16-Wheel Truck",
            "16 wheel": "16-Wheel Truck",
            
            # Special types
            "car-carrier": "Car-Carrier",
            "car carrier": "Car-Carrier",
            "part-load": "Part-Load",
            "part load": "Part-Load",
        }

        if not self.booking_data.vehicle_type:
            from fuzzywuzzy import fuzz
            
            # Try fuzzy matching for each word/phrase in user text
            best_match = None
            best_score = 0
            best_vehicle = None
            
            # Split text into words and create n-grams (1-4 words)
            words = text_lower.split()
            for i in range(len(words)):
                for j in range(i + 1, min(i + 5, len(words) + 1)):  # Check up to 4-word phrases
                    phrase = " ".join(words[i:j])
                    
                    # Check against all vehicle keywords
                    for keyword, vehicle_name in vehicle_keywords.items():
                        # Use partial ratio for better matching
                        score = fuzz.partial_ratio(phrase, keyword)
                        
                        # If score is high enough and better than previous matches
                        if score > best_score and score >= 85:  # Increased to 85% for better accuracy
                            best_score = score
                            best_match = keyword
                            best_vehicle = vehicle_name
            
            # If we found a good match, use it (allow updates if confidence is higher)
            if best_vehicle and best_score >= 85:
                self.booking_data.vehicle_type = best_vehicle
                if self.logger:
                    self.logger.log_booking_update("vehicle_type", best_vehicle)
                    self.logger.log_info(f"Fuzzy matched '{best_match}' with {best_score}% confidence")
        
        # Also try to extract from confirmation: "truck type X"
        # Updated regex to be more robust
        truck_type_pattern = r'truck\s+(?:type\s+)?([a-zA-Z0-9\s]+?)(?:,|body|\s+open|\s+container|\.|$)'
        truck_match = re.search(truck_type_pattern, text_lower)
        if truck_match:
            truck_mentioned = truck_match.group(1).strip()
            # Try fuzzy match on this
            from fuzzywuzzy import fuzz
            best_score = 0
            best_vehicle = None
            
            for keyword, vehicle_name in vehicle_keywords.items():
                # Use ratio for short strings, partial_ratio for longer
                score = fuzz.ratio(truck_mentioned.lower(), keyword)
                if score > best_score and score >= 65:  # Lower threshold for explicit confirmation mentions
                    best_score = score
                    best_vehicle = vehicle_name
            
            if best_vehicle:
                self.booking_data.vehicle_type = best_vehicle
                if self.logger:
                    self.logger.log_booking_update("vehicle_type", best_vehicle)
                    self.logger.log_info(f"Extracted from confirmation: '{truck_mentioned}' → {best_vehicle}")
        
        # Fallback: Check for feet sizes using regex
        if not self.booking_data.vehicle_type:
            feet_pattern = r'(\d+)\s*(?:feet|ft|foot)'
            feet_match = re.search(feet_pattern, text_lower)
            if feet_match:
                feet = feet_match.group(1)
                self.booking_data.vehicle_type = f"{feet} Feet"
                if self.logger:
                    self.logger.log_booking_update("vehicle_type", self.booking_data.vehicle_type)
            elif "truck" in text_lower:
                self.booking_data.vehicle_type = "Truck"
                if self.logger:
                    self.logger.log_booking_update("vehicle_type", "Truck")
        
        # Detect material/goods type (expanded list)
        materials = [
            "steel", "cement", "fmcg", "machinery", "furniture", "electronics", 
            "food", "grain", "coal", "books", "paper", "textile", "clothes",
            "plastic", "metal", "wood", "glass", "chemicals"
        ]
        for material in materials:
            if material in text_lower and not self.booking_data.goods_type:
                self.booking_data.goods_type = material.title()
                if self.logger:
                    self.logger.log_booking_update("goods_type", self.booking_data.goods_type)
                break
        
        # Detect trip date and convert to YYYY-MM-DD format
        from datetime import datetime, timedelta
        
        if not self.booking_data.trip_date:
            if "today" in text_lower or "now" in text_lower:
                date_obj = datetime.now()
                self.booking_data.trip_date = date_obj.strftime("%Y-%m-%d")
                if self.logger:
                    self.logger.log_booking_update("trip_date", self.booking_data.trip_date)
            elif "tomorrow" in text_lower:
                date_obj = datetime.now() + timedelta(days=1)
                self.booking_data.trip_date = date_obj.strftime("%Y-%m-%d")
                if self.logger:
                    self.logger.log_booking_update("trip_date", self.booking_data.trip_date)
            elif "day after tomorrow" in text_lower or "overmorrow" in text_lower:
                date_obj = datetime.now() + timedelta(days=2)
                self.booking_data.trip_date = date_obj.strftime("%Y-%m-%d")
                if self.logger:
                    self.logger.log_booking_update("trip_date", self.booking_data.trip_date)
    
    def _detect_confirmation(self, text: str):
        """
        Detect confirmation or rejection keywords in user text.
        
        Args:
            text: User's spoken text
        """
        text_lower = text.lower()
        
        # Expanded confirmation keywords
        confirmation_keywords = [
            "yes", "yeah", "yep", "ok", "okay", "correct", "right", "sure", 
            "fine", "perfect", "that's right", "confirmed", "done", 
            "absolutely", "exactly"
        ]
        
        # Detect confirmation
        if any(keyword in text_lower for keyword in confirmation_keywords):
            if self.booking_data.confirmation_status == "pending":
                self.booking_data.confirmation_status = "confirmed"
                if self.logger:
                    self.logger.log_confirmation_status("confirmed")
        
        # Detect rejection
        rejection_keywords = ["no", "not interested", "cancel", "don't want", "not now"]
        if any(keyword in text_lower for keyword in rejection_keywords):
            if self.booking_data.confirmation_status == "pending":
                self.booking_data.confirmation_status = "not_interested"
                if self.logger:
                    self.logger.log_confirmation_status("not_interested")
    
    def check_booking_confirmed_marker(self, response_text: str) -> bool:
        """
        Check if the LLM response contains the BOOKING_CONFIRMED marker.
        This indicates the customer has confirmed and we should send to API.
        
        Args:
            response_text: The LLM's response text
            
        Returns:
            True if BOOKING_CONFIRMED marker is present
        """
        return "BOOKING_CONFIRMED" in response_text
    
    def get_booking_data(self) -> BookingData:
        """
        Get the current booking data.
        
        Returns:
            BookingData object with collected information
        """
        return self.booking_data
    
    def is_booking_complete(self) -> bool:
        """
        Check if all required booking information has been collected.
        
        Returns:
            True if booking is complete, False otherwise
        """
        return self.booking_data.is_complete()
    
    def get_conversation_summary(self) -> str:
        """
        Get a summary of the conversation for debugging.
        
        Returns:
            String summary of conversation
        """
        user_messages = [msg for msg in self.conversation_history if msg["role"] == "user"]
        assistant_messages = [msg for msg in self.conversation_history if msg["role"] == "assistant"]
        
        return f"Conversation: {len(user_messages)} user messages, {len(assistant_messages)} assistant messages"
