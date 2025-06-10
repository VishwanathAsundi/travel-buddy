from openai import AzureOpenAI
from config import Config
import json
import logging

class AzureOpenAIService:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=Config.AZURE_OPENAI_API_KEY,
            api_version=Config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=Config.AZURE_OPENAI_ENDPOINT
        )
        self.deployment_name = Config.AZURE_OPENAI_DEPLOYMENT_NAME
    
    def generate_travel_recommendations(self, place_data, query_type, user_query, context_history=[]):
        """Generate travel recommendations based on place data and query type"""
        
        system_prompt = self._get_system_prompt(query_type)
        user_prompt = self._create_user_prompt(place_data, user_query, query_type)
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add context history
        for msg in context_history[-Config.MAX_CONTEXT_MESSAGES:]:
            messages.append(msg)
        
        messages.append({"role": "user", "content": user_prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                user=json.dumps({"appkey": Config.AZURE_APP_KEY}),
                temperature=0.7,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            logging.error(f"Azure OpenAI API error: {str(e)}")
            return f"Sorry, I encountered an error generating recommendations: {str(e)}"
    
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