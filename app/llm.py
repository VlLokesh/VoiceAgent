"""
LLM integration module for the voice agent.
Manages conversation with OpenAI API and extracts booking information.
"""

import os
import re
import requests
from typing import Dict, Optional, Tuple
from prompt import SYSTEM_PROMPT, BookingData


class LLMAgent:
    """Manages LLM interactions and conversation state."""
    
    def __init__(self, api_key: str = None, model: str = None):
        """
        Initialize LLM agent.
        
        Args:
            api_key: OpenAI API key (reads from env if not provided)
            model: OpenAI model to use (default: gpt-4o-mini)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
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
        
        # If no API key, use echo mode
        if not self.api_key:
            return f"[Echo Mode] You said: {user_text}"
        
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
            
            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })
            
            return response_text
            
        except Exception as e:
            print(f"❌ LLM error: {e}")
            return "I'm having trouble processing that right now. Could you try again?"
    
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
            "temperature": 0.7,
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
        
        # Simple keyword-based extraction (can be enhanced)
        # The LLM will handle the actual conversation and confirmation
        
        # Detect body type
        if "open" in text_lower and self.booking_data.body_type is None:
            self.booking_data.body_type = "Open"
        elif "container" in text_lower and self.booking_data.body_type is None:
            self.booking_data.body_type = "Container"
        
        # Detect vehicle type mentions
        if "truck" in text_lower and self.booking_data.vehicle_type is None:
            self.booking_data.vehicle_type = "Truck"
        
        # Note: More sophisticated extraction would use NER or LLM-based extraction
        # For now, we rely on the LLM to guide the conversation and ask for clarifications
    
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
