import streamlit as st
import logging
from datetime import datetime
from utils.helpers import get_distance_options
from utils.pdf_export_helper import create_pdf_report

class SidebarManager:
    """Manages the sidebar UI and interactions"""
    
    def __init__(self):
        self.query_types = {
            "🏛️ Tourist Places": "tourist_places",
            "🍽️ Restaurants": "restaurants", 
            "🎯 Activities": "activities",
            "🏨 Hotels & Resorts": "hotels"
        }
    
    def render_sidebar(self):
        """Render the complete sidebar and return search parameters"""
        with st.sidebar:
            # Search options section
            search_params = self._render_search_options()
            
            # PDF export section
            if st.session_state.search_results:
                self._render_pdf_export_section()
            
            # Conversation management section
            self._render_conversation_section()
            
            return search_params
    
    def _render_search_options(self):
        """Render search options section"""
        st.header("🎯 Search Options")
        
        # Location input
        location = st.text_input("📍 Enter Location", placeholder="e.g., Gokarna, Hampi, Mysore..")
        
        # Search radius
        distance_options = get_distance_options()
        selected_distance = st.selectbox("🔍 Search Radius", list(distance_options.keys()), index=2)
        search_radius = distance_options[selected_distance]
        
        # Query type selection
        selected_query_type = st.selectbox("🎭 What are you looking for?", list(self.query_types.keys()))
        query_type = self.query_types[selected_query_type]
        
        # Search button
        search_clicked = st.button("🔍 Search", type="primary", use_container_width=True)
        
        return {
            'location': location,
            'search_radius': search_radius,
            'selected_query_type': selected_query_type,
            'query_type': query_type,
            'search_clicked': search_clicked
        }
    
    def _render_pdf_export_section(self):
        """Render PDF export section"""
        st.markdown("---")
        st.header("📄 Export Options")
        
        try:
            # Ensure conversation_history exists, even if empty
            conversation_history = st.session_state.get('conversation_history', [])
            
            # Create PDF with proper error handling
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
            
            # Show different success messages based on content
            if conversation_history and len(conversation_history) > 2:
                st.success("✅ PDF ready with search results and conversation history!")
            else:
                st.success("✅ PDF ready with search results!")
        
        except Exception as e:
            logging.error(f"Error creating PDF: {str(e)}")
            st.error(f"❌ Error creating PDF: {str(e)}")
            st.info("💡 Try searching again or clearing chat history if the error persists.")
    
    def _render_conversation_section(self):
        """Render conversation management section"""
        st.header("💬 Conversation")
        
        if st.button("🗑️ Clear History"):
            # Keep initial search results but clear follow-up conversations
            if len(st.session_state.conversation_history) > 2:
                st.session_state.conversation_history = st.session_state.conversation_history[:2]
            else:
                st.session_state.conversation_history = []
            
            # Clear context history (assuming context service is available)
            # This would need to be passed in or accessed differently
            st.session_state.processing_question = False
            st.success("Chat history cleared!")
            st.rerun()
        
        # Display conversation count
        history_count = len(st.session_state.get('conversation_history', []))
        if history_count > 2:
            follow_up_count = history_count - 2
            st.info(f"Follow-up messages: {follow_up_count}")
        else:
            st.info("No follow-up conversations yet")