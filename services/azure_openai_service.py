from openai import AzureOpenAI
from config import Config
import json
import logging
import requests
import time
import base64
import threading

# Global token storage
token_data = {"access_token": None, "expires_at": 0}  # Unix timestamp

class AzureOpenAIService:
    def __init__(self):
        self.deployment_name = Config.AZURE_OPENAI_DEPLOYMENT_NAME
        self._token_lock = threading.Lock()
        
        # Initialize client with the first token
        self.client = self._get_openai_client()
    
    def _is_token_expired(self):
        """Check if the current token is expired"""
        return time.time() >= token_data["expires_at"]
    
    def _generate_access_token(self):
        """Generate new access token using client credentials"""
        payload = "grant_type=client_credentials"
        value = base64.b64encode(f"{Config.CLIENT_ID}:{Config.CLIENT_SECRET}".encode("utf-8")).decode("utf-8")
        
        headers = {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {value}",
        }
        
        try:
            token_response = requests.post(Config.OAUTH_URL, headers=headers, data=payload)
            
            if token_response.status_code == 200:
                response_data = token_response.json()
                token_data["access_token"] = response_data.get("access_token")
                # Add 5-minute buffer to expiry time
                expires_in = response_data.get("expires_in", 3600)
                token_data["expires_at"] = time.time() + expires_in - 300
                
                logging.info("Successfully obtained new access token")
                return True
            else:
                logging.error(f"Token generation failed: {token_response.status_code} - {token_response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Error generating access token: {str(e)}")
            return False
    
    def _get_access_token(self):
        """Get valid access token, refreshing if necessary"""
        with self._token_lock:
            if self._is_token_expired():
                logging.info("Token expired. Fetching new token...")
                if not self._generate_access_token():
                    raise Exception("Failed to generate access token")
            else:
                logging.debug("Using cached token.")
            
            return token_data["access_token"]
    
    def _get_openai_client(self):
        """Get OpenAI client with current access token"""
        access_token = self._get_access_token()
        
        return AzureOpenAI(
            azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
            api_version=Config.AZURE_OPENAI_API_VERSION,
            api_key=access_token,
            # Add other configuration if needed
        )
    
    def _ensure_valid_client(self):
        """Ensure we have a valid client with fresh token"""
        if self._is_token_expired():
            logging.info("Token expired, refreshing client...")
            self.client = self._get_openai_client()
    
    def generate_travel_recommendations(self, place_data, query_type, user_query, context_history=[]):
        """Generate travel recommendations based on place data and query type"""
        
        system_prompt = self._get_system_prompt(query_type)
        user_prompt = self._create_user_prompt(place_data, user_query, query_type)
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add context history
        for msg in context_history[-Config.MAX_CONTEXT_MESSAGES:]:
            messages.append(msg)
        
        messages.append({"role": "user", "content": user_prompt})
        
        max_retries = 1
        for attempt in range(max_retries):
            try:
                # Ensure we have a valid client before making the call
                self._ensure_valid_client()
                
                response = self.client.chat.completions.create(
                    model=self.deployment_name,
                    messages=messages,
                    user=json.dumps({"appkey": Config.AZURE_OPENAI_APP_KEY}),
                    temperature=0.7,
                    max_tokens=1500
                )
                
                return response.choices[0].message.content
            
            except Exception as e:
                error_message = str(e).lower()
                
                # Check if it's an authentication error
                if any(auth_error in error_message for auth_error in 
                       ['unauthorized', 'invalid_token', 'token_expired', 'authentication', '401']):
                    
                    if attempt < max_retries - 1:
                        logging.warning(f"Authentication error detected, refreshing token and retrying: {str(e)}")
                        # Force token refresh by setting expiry to past
                        token_data["expires_at"] = 0
                        self.client = self._get_openai_client()
                        continue
                    else:
                        logging.error(f"Authentication failed after {max_retries} attempts: {str(e)}")
                        return "Sorry, I encountered an authentication error. Please try again later."
                
                # For non-auth errors, log and return error message
                logging.error(f"Azure OpenAI API error: {str(e)}")
                return f"Sorry, I encountered an error generating recommendations: {str(e)}"
        
        return "Sorry, I encountered an unexpected error. Please try again."
    
    def _get_system_prompt(self, query_type):
        base_prompt = """You are Travel Buddy, an expert travel assistant that provides detailed, helpful, and personalized travel recommendations. You have access to real-time data about places, restaurants, hotels, and activities."""
        
        type_specific_prompts = {
            "tourist_places": """
            Focus on providing information about:
            - Top tourist attractions and landmarks
            - Hidden gems and local favorites
            - Cultural and historical sites
            - Natural attractions
            - Best times to visit each place
            - Estimated time needed for each attraction
            """,
            "restaurants": """
            Focus on providing information about:
            - Restaurant names, cuisine types, and specialties
            - Price ranges and estimated costs per person
            - Popular dishes and must-try items
            - Ambiance and dining experience
            - Ratings and reviews summary
            - Distance from the main location
            """,
            "activities": """
            Focus on providing information about:
            - Adventure activities and sports
            - Cultural experiences and workshops
            - Entertainment and nightlife
            - Seasonal activities
            - Age-appropriate recommendations
            - Cost estimates and booking requirements
            """,
            "hotels": """
            Focus on providing information about:
            - Hotel names, star ratings, and types
            - Price ranges per night
            - Key amenities and features
            - Location advantages
            - Guest rating summaries
            - Booking recommendations
            """
        }
        
        return base_prompt + type_specific_prompts.get(query_type, "")
    
    def _create_user_prompt(self, place_data, user_query, query_type):
        prompt = f"User Query: {user_query}\n\n"
        prompt += f"Query Type: {query_type}\n\n"
        
        if place_data:
            prompt += "Available Data:\n"
            for i, place in enumerate(place_data[:10], 1):
                prompt += f"\n{i}. {place.get('name', 'Unknown')}\n"
                prompt += f"   Rating: {place.get('rating', 'N/A')}\n"
                prompt += f"   Address: {place.get('vicinity', place.get('formatted_address', 'N/A'))}\n"
                
                if 'price_level' in place:
                    price_levels = {1: "$", 2: "$$", 3: "$$$", 4: "$$$$", 5: "$$$$$"}
                    prompt += f"   Price Level: {price_levels.get(place['price_level'], 'N/A')}\n"
                
                if 'types' in place:
                    prompt += f"   Categories: {', '.join(place['types'][:3])}\n"
        
        prompt += f"\n\nPlease provide detailed recommendations for {query_type} based on this data. Format your response in a clear, organized manner with specific details about each recommendation."
        
        return prompt

# Utility functions for testing
def get_access_token():
    """Utility function to get access token (for testing)"""
    service = AzureOpenAIService()
    return service._get_access_token()

if __name__ == "__main__":
    # Test token generation
    try:
        print("Testing token generation...")
        token = get_access_token()
        print(f"Token obtained: {token[:20]}..." if token else "Failed to get token")
        
        # Test service initialization
        print("Testing service initialization...")
        service = AzureOpenAIService()
        print("Service initialized successfully!")
        
    except Exception as e:
        print(f"Error: {e}")