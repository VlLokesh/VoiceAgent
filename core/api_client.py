"""
API Client for sending booking data to DropTruck backend.
"""

import requests
import json


class DropTruckAPIClient:
    """Client for interacting with DropTruck API."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        """
        Initialize API client.
        Args:
            base_url: Base URL of the DropTruck API
        """
        self.base_url = base_url
        self.endpoint = f"{base_url}/agent-newindent"
    
    def send_booking(self, booking_data: dict) -> bool:
        """
        Send booking data to DropTruck API.
        Args:
            booking_data: Dictionary containing booking information
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare payload
            payload = {
                "name": booking_data.get("customer_name", "Lokesh"),
                "contact": booking_data.get("contact", "9066542031"),
                "pickup_location": booking_data.get("pickup_location", ""),
                "drop_location": booking_data.get("drop_location", ""),
                "truck_type": booking_data.get("vehicle_type", ""),
                "body_type": booking_data.get("body_type", ""),
                "material": booking_data.get("goods_type", ""),
                "required_date": booking_data.get("trip_date", "")
            }
            
            print(f"\n📤 Sending booking to API: {self.endpoint}")
            print(f"📦 Payload: {json.dumps(payload, indent=2)}")
            
            # Send POST request
            response = requests.post(
                self.endpoint,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=10
            )
            
            # Check response
            if response.status_code == 200:
                print(f"✅ Booking sent successfully!")
                print(f"📥 Response: {response.json()}")
                return True
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"📥 Response: {response.text}")
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection Error: Could not connect to {self.endpoint}")
            print(f"💡 Make sure the DropTruck API server is running")
            return False
        except requests.exceptions.Timeout:
            print(f"❌ Timeout: API request took too long")
            return False
        except Exception as e:
            print(f"❌ Error sending booking: {e}")
            import traceback
            traceback.print_exc()
            return False
