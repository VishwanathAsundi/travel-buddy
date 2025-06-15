import streamlit as st
from utils.helpers import display_places_data, format_ai_response
from handlers.location_handler import handle_location_search, handle_current_location_search

def render_main_content(services, search_params):
    """Render the main content area."""
    location = search_params.get('location')
    current_loc_search = search_params.get('current_loc_search')
    selected_query_type = search_params.get('selected_query_type')
    query_type = search_params.get('query_type')
    search_radius = search_params.get('search_radius')
    search_clicked = search_params.get('search_clicked')

    lat = st.session_state.get('lat', None)
    lng = st.session_state.get('lng', None)

    if not lat or not lng:
        # Attempt to read coordinates from session_state or getLocation() key
        coords_data = (
            st.session_state.get("getLocation()") or 
            {}
        )
        coords = coords_data.get("coords", {}) if "coords" in coords_data else coords_data

        lat = coords.get("latitude", None)
        lng = coords.get("longitude", None)

        if lat and lng:
            st.session_state['lat'] = lat
            st.session_state['lng'] = lng

    # Override with most reliable sources if present
    if st.session_state.get("current_location_lat") and st.session_state.get("current_location_lng"):
        lat = st.session_state["current_location_lat"]
        lng = st.session_state["current_location_lng"]
    elif st.session_state.get("manual_lat") and st.session_state.get("manual_lng"):
        lat = st.session_state["manual_lat"]
        lng = st.session_state["manual_lng"]

    # ----- Coordinate-Based Search -----
    if (search_clicked or current_loc_search) and lat and lng:
        with st.spinner(f"🔍 Searching for {selected_query_type.lower()} near coordinates ({lat:.4f}, {lng:.4f})..."):
            handle_current_location_search(
                services,
                lat,
                lng,
                query_type,
                selected_query_type,
                search_radius
            )

    # ----- Location-Based Search -----
    elif search_clicked and location:
        if st.session_state.get("last_search") != (location, query_type):
            with st.spinner(f"🔍 Searching for {selected_query_type.lower()} in {location}..."):
                handle_location_search(
                    services,
                    location,
                    query_type,
                    selected_query_type,
                    search_radius
                )

    # ----- Welcome or Results -----
    if not location and not st.session_state.get("search_results"):
        render_welcome_screen()
    elif st.session_state.get("search_results"):
        render_search_results(services, selected_query_type)


def render_welcome_screen():
    """Render the welcome screen with instructions"""
    st.info("👈 Please enter a location or use your current location in the sidebar to get started!")
    
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
    
    # Current Location Instructions
    st.subheader("📍 How to use Current Location:")
    st.markdown("""
    1. **Click "Get Current Location"** in the sidebar
    2. **Allow location access** when prompted by your browser
    3. **Wait for coordinates** to be displayed
    4. **Choose your search type** (Tourist Places, Restaurants, etc.)
    5. **Click "Search Current"** to find places near you
    """)

def render_search_results(services, selected_query_type):
    """Render search results"""
    results = st.session_state.search_results
    
    # Show location info (including coordinates if available)
    location_display = results['location']
    if 'coordinates' in results:
        coords = results['coordinates']
        location_display += f" (📍 {coords['lat']:.4f}, {coords['lng']:.4f})"
    
    st.header(f"🌟 Results for {location_display}")
    
    # AI Recommendations
    st.subheader("🤖 AI Travel Recommendations")
    formatted_response = format_ai_response(results['ai_response'])
    st.markdown(formatted_response)
    
    # Raw data display
    st.markdown("### 📊 View Detailed Place Information")
    display_places_data(results['places_data'], selected_query_type)
    
    # Nearby places suggestion (only for location-based searches)
    if results['query_type'] == "tourist_places" and 'coordinates' not in results:
        st.subheader("🗺️ Nearby Places to Explore")
        nearby_places = services['places'].search_nearby_places(results['location'], 70)
        if nearby_places:
            nearby_names = [place.get('name', 'Unknown') for place in nearby_places[:10]]
            st.write("Consider visiting these nearby locations: " + ", ".join(nearby_names))