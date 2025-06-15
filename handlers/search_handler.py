import streamlit as st
import logging
from utils.session_manager import SessionManager

class SearchHandler:
    """Handles search operations and results processing"""
    
    def __init__(self, services):
        self.services = services
        self.session_manager = SessionManager()
    
    def handle_search(self, search_params):
        """Handle the search operation"""
        location = search_params['location']
        query_type = search_params['query_type']
        selected_query_type = search_params['selected_query_type']
        search_radius = search_params['search_radius']
        
        with st.spinner(f"🔍 Searching for the best {selected_query_type.lower()} in {location}..."):
            try:
                # Search for places
                places_data = self.services['places'].search_places(location, query_type, search_radius)
                
                if places_data:
                    # Generate AI recommendations
                    ai_response = self._generate_ai_recommendations(location, query_type, places_data)
                    
                    # Save to context
                    user_query = self._create_user_query(location, query_type)
                    self._save_to_context(user_query, ai_response, location, query_type, len(places_data))
                    
                    # Update session state
                    self.session_manager.update_search_results(location, query_type, places_data, ai_response)
                    self.session_manager.initialize_conversation_with_search(user_query, ai_response)
                    
                    # Handle nearby places for tourist attractions
                    if query_type == "tourist_places":
                        self._suggest_nearby_places(location)
                        
                else:
                    st.error(f"No {selected_query_type.lower()} found in {location}. Try a different location or search type.")
                    
            except Exception as e:
                logging.error(f"Error during search: {str(e)}")
                st.error(f"An error occurred during search: {str(e)}")
    
    def _generate_ai_recommendations(self, location, query_type, places_data):
        """Generate AI recommendations for the search results"""
        context_history = self.services['context'].get_context_messages()
        user_query = self._create_user_query(location, query_type)
        
        return self.services['openai'].generate_travel_recommendations(
            places_data, query_type, user_query, context_history
        )
    
    def _create_user_query(self, location, query_type):
        """Create the user query based on location and query type"""
        if query_type == 'activities':
            return f"Show me the best activities in {location}, exclude spas, hotels, temples, restaurants, accommodation, and shopping. Only show actual activities and experiences."
        else:
            return f"Show me the best {query_type.lower()} in {location}"
    
    def _save_to_context(self, user_query, ai_response, location, query_type, results_count):
        """Save the search results to context manager"""
        self.services['context'].add_message("user", user_query, {
            "location": location,
            "query_type": query_type,
            "results_count": results_count
        })
        self.services['context'].add_message("assistant", ai_response)
    
    def _suggest_nearby_places(self, location):
        """Get and store nearby places suggestions"""
        try:
            nearby_places = self.services['places'].search_nearby_places(location, 50)
            if nearby_places:
                # Store nearby places in session state for later use
                st.session_state.nearby_places = nearby_places
        except Exception as e:
            logging.warning(f"Could not fetch nearby places: {str(e)}")
            st.session_state.nearby_places = None