import streamlit as st
import logging
from services.azure_openai_service import AzureOpenAIService
from services.google_places_service import GooglePlacesService
from services.context_manager import ContextManager
from utils.helpers import display_places_data, create_summary_card, format_ai_response, get_distance_options
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)

# Page configuration
st.set_page_config(
    page_title="Travel Buddy 🧳",
    page_icon="🧳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize services
@st.cache_resource
def init_services():
    return {
        'openai': AzureOpenAIService(),
        'places': GooglePlacesService(),
        'context': ContextManager()
    }

services = init_services()

def main():
    # Initialize session state variables
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []

    if 'last_search' not in st.session_state:
        st.session_state.last_search = None

    if 'search_results' not in st.session_state:
        st.session_state.search_results = None

    st.title("🧳 Travel Buddy")
    st.markdown("*Your AI-powered travel companion for discovering amazing places, restaurants, activities, and accommodations.*")
    
    # Sidebar
    with st.sidebar:
        st.header("🎯 Search Options")
        
        # Location input
        location = st.text_input("📍 Enter Location", placeholder="e.g., Paris, New York, Tokyo")
        
        # Search radius
        distance_options = get_distance_options()
        selected_distance = st.selectbox("🔍 Search Radius", list(distance_options.keys()), index=2)
        search_radius = distance_options[selected_distance]
        
        # Query type selection
        query_types = {
            "🏛️ Tourist Places": "tourist_places",
            "🍽️ Restaurants": "restaurants", 
            "🎯 Activities": "activities",
            "🏨 Hotels & Resorts": "hotels"
        }
        
        selected_query_type = st.selectbox("🎭 What are you looking for?", list(query_types.keys()))
        query_type = query_types[selected_query_type]
        
        # Search button
        search_clicked = st.button("🔍 Search", type="primary", use_container_width=True)
        
        # Context management
        st.header("💬 Conversation")
        if st.button("🗑️ Clear History"):
            services['context'].clear_history()
            st.success("Conversation history cleared!")
            st.rerun()
        
        # Display conversation count
        history_count = len(st.session_state.get('conversation_history', []))
        st.info(f"Messages in history: {history_count}")
    
    # Main content area
    if not location:
        st.info("👈 Please enter a location in the sidebar to get started!")
        
        # Display sample queries
        st.subheader("🌟 What Travel Buddy can help you with:")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **🏛️ Tourist Places**
            - Top attractions and landmarks
            - Hidden gems and local favorites
            - Cultural and historical sites
            - Best visiting times
            """)
            
            st.markdown("""
            **🍽️ Restaurants**
            - Local cuisine recommendations
            - Price ranges and cost estimates
            - Popular dishes to try
            - Restaurant ratings and reviews
            """)
        
        with col2:
            st.markdown("""
            **🎯 Activities**
            - Adventure and outdoor activities
            - Cultural experiences
            - Entertainment options
            - Seasonal recommendations
            """)
            
            st.markdown("""
            **🏨 Hotels & Resorts**
            - Accommodation options
            - Price ranges per night
            - Amenities and features
            - Location advantages
            """)
        
        return
    
    if search_clicked or st.session_state.get('last_search') != (location, query_type):
        with st.spinner(f"🔍 Searching for {selected_query_type.lower()} in {location}..."):
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
    
    # Display results
    if 'search_results' in st.session_state:
        results = st.session_state.search_results
        
        st.header(f"🌟 Results for {results['location']}")
        
        # AI Recommendations
        st.subheader("🤖 AI Travel Recommendations")
        formatted_response = format_ai_response(results['ai_response'])
        st.markdown(formatted_response)
        
        # Raw data display
        st.markdown("### 📊 View Detailed Place Information")
        display_places_data(results['places_data'], selected_query_type)
        
        # Nearby places suggestion
        if query_type == "tourist_places":
            st.subheader("🗺️ Nearby Places to Explore")
            nearby_places = services['places'].search_nearby_places(location, 50)
            if nearby_places:
                nearby_names = [place.get('name', 'Unknown') for place in nearby_places[:5]]
                st.write("Consider visiting these nearby locations: " + ", ".join(nearby_names))
    
    # Chat interface for follow-up questions
    st.header("💬 Ask Follow-up Questions")
    
    # Display recent conversation
    if st.session_state.get('conversation_history'):
        with st.expander("📖 Recent Conversation", expanded=False):
            for msg in st.session_state.conversation_history[-6:]:
                role_icon = "🧑‍💼" if msg['role'] == 'user' else "🤖"
                st.markdown(f"**{role_icon} {msg['role'].title()}:** {msg['content'][:200]}...")
    
    # Follow-up question input
    follow_up_question = st.text_input(
        "Ask a follow-up question about your travel plans:",
        placeholder="e.g., What's the best time to visit these places? Any budget-friendly options?"
    )
    
    if st.button("💬 Ask Question") and follow_up_question:
        if 'search_results' in st.session_state:
            with st.spinner("🤔 Thinking..."):
                context_history = services['context'].get_context_messages()
                
                ai_response = services['openai'].generate_travel_recommendations(
                    st.session_state.search_results['places_data'],
                    st.session_state.search_results['query_type'],
                    follow_up_question,
                    context_history
                )
                
                # Save to context
                services['context'].add_message("user", follow_up_question)
                services['context'].add_message("assistant", ai_response)
                
                # Display response
                st.subheader("🤖 Travel Buddy's Response")
                st.markdown(format_ai_response(ai_response))
                
                st.rerun()
        else:
            st.warning("Please search for a location first before asking follow-up questions.")

    # Footer
    st.markdown("---")
    st.markdown("*Built with ❤️ using Streamlit, Azure OpenAI, and Google Places API*")

if __name__ == "__main__":
    main()