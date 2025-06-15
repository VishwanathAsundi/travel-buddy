import streamlit as st
import logging
from datetime import datetime
from utils.helpers import get_distance_options
from utils.pdf_export_helper import create_pdf_report
from utils.session_state import reset_conversation_history
from ui.location_components import render_current_location_component
from handlers.location_handler import handle_current_location_search, handle_location_search

def render_sidebar(services):
    """Render the sidebar with search options and controls"""
    with st.sidebar:
        st.header("🎯 Search Options")
        
        # Current Location Section
        st.subheader("📍 Location Options")

        st.markdown("**Option 1: Get your current location**")
        
        # Current location component
        render_current_location_component()
        
        st.markdown("**Option 2: Enter Location Manually**")
        
        # Location input
        location = st.text_input("📍 Enter Location", placeholder="e.g., Gokarna, Hampi, Mysore..")
        
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
        
        # Search buttons
        col1, col2 = st.columns(2)
        with col1:
            search_clicked = st.button("🔍 Search Location", type="primary", use_container_width=True)
        
        with col2:
            current_loc_search = st.button("📍 Search Current", type="secondary", use_container_width=True)
        
        # Handle searches
        search_params = {
            'location': location,
            'query_type': query_type,
            'selected_query_type': selected_query_type,
            'search_radius': search_radius,
            'search_clicked': search_clicked,
            'current_loc_search': current_loc_search
        }
        
        # Handle current location search
        # if current_loc_search:
        #     st.markdown("""
        #     <script>
        #     const lat = sessionStorage.getItem('current_lat');
        #     const lng = sessionStorage.getItem('current_lng');
            
        #     if (lat && lng) {
        #         window.parent.postMessage({
        #             type: 'streamlit:setComponentValue',
        #             value: {lat: parseFloat(lat), lng: parseFloat(lng)}
        #         }, '*');
        #     } else {
        #         alert('Please get your current location first using the "Get Current Location" button above.');
        #     }
        #     </script>
        #     """, unsafe_allow_html=True)
        #     st.info("💡 Make sure to click 'Get Current Location' first, then try 'Search Current' again.")
        
        # Manual coordinate input
        render_manual_coordinates_section(services, query_type, selected_query_type, search_radius)
        
        # PDF Download section
        render_pdf_download_section()
        
        # Conversation management
        render_conversation_management(services)
    
    return search_params

def render_manual_coordinates_section(services, query_type, selected_query_type, search_radius):
    """Render manual coordinates input section"""
    with st.expander("🗺️ Manual Coordinates (Optional)"):
        col_lat, col_lng = st.columns(2)
        with col_lat:
            manual_lat = st.number_input("Latitude", format="%.6f", step=0.000001)
        with col_lng:
            manual_lng = st.number_input("Longitude", format="%.6f", step=0.000001)
        
        if st.button("🎯 Search Manual Coordinates"):
            if manual_lat != 0.0 and manual_lng != 0.0:
                with st.spinner(f"🔍 Searching for {selected_query_type.lower()} near coordinates..."):
                    handle_current_location_search(
                        services, manual_lat, manual_lng, 
                        query_type, selected_query_type, search_radius
                    )
            else:
                st.error("Please enter valid coordinates")

def render_pdf_download_section():
    """Render PDF download section"""
    if st.session_state.search_results:
        st.markdown("---")
        st.header("📄 Export Options")
    
        try:
            conversation_history = st.session_state.get('conversation_history', [])
            
            pdf_buffer = create_pdf_report(
                st.session_state.search_results, 
                conversation_history
            )
            
            # Generate filename
            location_clean = st.session_state.search_results['location'].replace(' ', '_').replace(',', '').replace('.', '')
            filename = f"travel_buddy_{location_clean}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_buffer,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
                type="secondary"
            )
            
            if conversation_history and len(conversation_history) > 2:
                st.success("✅ PDF ready with search results and conversation history!")
            else:
                st.success("✅ PDF ready with search results!")
    
        except Exception as e:
            logging.error(f"Error creating PDF: {str(e)}")
            st.error(f"❌ Error creating PDF: {str(e)}")
            st.info("💡 Try searching again or clearing chat history if the error persists.")

def render_conversation_management(services):
    """Render conversation management section"""
    st.header("💬 Conversation")
    if st.button("🗑️ Clear History"):
        reset_conversation_history()
        services['context'].clear_history()
        st.success("Chat history cleared!")
        st.rerun()
    
    # Display conversation count
    history_count = len(st.session_state.get('conversation_history', []))
    if history_count > 2:
        follow_up_count = history_count - 2
        st.info(f"Follow-up messages: {follow_up_count}")
    else:
        st.info("No follow-up conversations yet")