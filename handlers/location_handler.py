import streamlit as st
import logging
import time

def handle_current_location_search(services, lat, lng, query_type, selected_query_type, search_radius):
    """Handle search using current location coordinates"""
    try:
        # Get location name from coordinates
        location_name = services['places'].get_location_name_from_coords(lat, lng)
        
        if not location_name:
            location_name = f"Current Location ({lat:.4f}, {lng:.4f})"
        
        # Search for places using coordinates
        places_data = services['places'].search_places_by_coords(lat, lng, query_type, search_radius)
        
        if places_data:
            # Generate AI recommendations
            context_history = services['context'].get_context_messages()
            user_query = f"Show me the best {selected_query_type.lower()} near my current location"
            
            ai_response = services['openai'].generate_travel_recommendations(
                places_data, query_type, user_query, context_history
            )
            
            # Save to context
            services['context'].add_message("user", user_query, {
                "location": location_name,
                "coordinates": {"lat": lat, "lng": lng},
                "query_type": query_type,
                "results_count": len(places_data)
            })
            services['context'].add_message("assistant", ai_response)
            
            # Store results in session state
            st.session_state.last_search = (f"coords_{lat}_{lng}", query_type)
            st.session_state.search_results = {
                'places_data': places_data,
                'ai_response': ai_response,
                'location': location_name,
                'query_type': query_type,
                'coordinates': {"lat": lat, "lng": lng}
            }
            
            # Clear previous conversation and add new search
            search_time = int(time.time() * 1000)
            st.session_state.conversation_history = [
                {
                    'role': 'user',
                    'content': user_query,
                    'timestamp': search_time,
                    'id': f"search_user_{search_time}"
                },
                {
                    'role': 'assistant',
                    'content': ai_response,
                    'timestamp': search_time + 1,
                    'id': f"search_assistant_{search_time}"
                }
            ]
            st.session_state.processing_question = False
            
            st.success(f"✅ Found {len(places_data)} {selected_query_type.lower()} near your current location!")
            st.rerun()
        else:
            st.error(f"No {selected_query_type.lower()} found near your current location. Try expanding the search radius.")
            
    except Exception as e:
        logging.error(f"Error searching with current location: {str(e)}")
        st.error(f"Error searching with current location: {str(e)}")

def handle_location_search(services, location, query_type, selected_query_type, search_radius):
    """Handle search for a specific location"""
    try:
        # Search for places
        places_data = services['places'].search_places(location, query_type, search_radius)
        
        if places_data:
            # Generate AI recommendations
            context_history = services['context'].get_context_messages()
            user_query = f"Show me the best {selected_query_type.lower()} in {location}"
            
            ai_response = services['openai'].generate_travel_recommendations(
                places_data, query_type, user_query, context_history
            )
            
            # Save to context
            services['context'].add_message("user", user_query, {
                "location": location,
                "query_type": query_type,
                "results_count": len(places_data)
            })
            services['context'].add_message("assistant", ai_response)
            
            # Store results in session state
            st.session_state.last_search = (location, query_type)
            st.session_state.search_results = {
                'places_data': places_data,
                'ai_response': ai_response,
                'location': location,
                'query_type': query_type
            }
            
            # Clear previous conversation and add new search
            search_time = int(time.time() * 1000)
            st.session_state.conversation_history = [
                {
                    'role': 'user',
                    'content': user_query,
                    'timestamp': search_time,
                    'id': f"search_user_{search_time}"
                },
                {
                    'role': 'assistant',
                    'content': ai_response,
                    'timestamp': search_time + 1,
                    'id': f"search_assistant_{search_time}"
                }
            ]
            st.session_state.processing_question = False
            return True
        else:
            st.error(f"No {selected_query_type.lower()} found in {location}. Try a different location or search type.")
            return False
    
    except Exception as e:
        logging.error(f"Error searching for location {location}: {str(e)}")
        st.error(f"Error searching for location: {str(e)}")
        return False