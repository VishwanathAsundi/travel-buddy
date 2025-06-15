import streamlit as st
from utils.helpers import display_places_data, format_ai_response

class UIComponents:
    """Reusable UI components for the Travel Buddy app"""
    
    def display_welcome_screen(self):
        """Display the welcome screen with feature information"""
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

        self.display_footer()
    
    def display_search_results(self, results, selected_query_type):
        """Display search results with AI recommendations and place data"""
        st.header(f"🌟 Results for {results['location']}")
        
        # AI Recommendations
        st.subheader("🤖 AI Travel Recommendations")
        formatted_response = format_ai_response(results['ai_response'])
        st.markdown(formatted_response)
        
        # Raw data display
        st.markdown("### 📊 View Detailed Place Information")
        display_places_data(results['places_data'], selected_query_type)
        
        # Nearby places suggestion for tourist places
        if results['query_type'] == "tourist_places":
            self._display_nearby_places_suggestion(results['location'])
    
    def _display_nearby_places_suggestion(self, location):
        """Display nearby places suggestion for tourist places"""
        # This would need access to the places service
        # For now, we'll show a placeholder
        st.subheader("🗺️ Nearby Places to Explore")
        st.info("💡 Consider exploring nearby locations for a complete travel experience!")
    
    def display_error_message(self, message, suggestion=None):
        """Display error message with optional suggestion"""
        st.error(f"❌ {message}")
        if suggestion:
            st.info(f"💡 {suggestion}")
    
    def display_success_message(self, message):
        """Display success message"""
        st.success(f"✅ {message}")
    
    def display_loading_spinner(self, message):
        """Display loading spinner with message"""
        return st.spinner(f"🔄 {message}")
    
    def display_footer(self):
        """Display app footer"""
        st.markdown("---")
        st.markdown("*Built with ❤️ by Traveller for Travellers*")
    
    def create_chat_message_html(self, message, is_user=True):
        """Create HTML for chat message display"""
        if is_user:
            return f"""
            <div style="display: flex; justify-content: flex-end; margin: 10px 0;">
                <div style="background: aliceblue;
                color: #000; padding: 12px 16px; border-radius: 18px 18px 5px 18px; 
                            max-width: 70%; box-shadow: 0 2px 8px rgba(0,0,0,0.15);">
                    <strong>You:</strong><br>{message}
                </div>
            </div>
            """
        else:
            return f"""
            <div style="display: flex; justify-content: flex-start; margin: 10px 0;">
                <div style="background: darkturquoise;
                            color: #000; padding: 12px 16px; border-radius: 18px 18px 18px 5px; 
                            max-width: 70%; box-shadow: 0 2px 8px rgba(0,0,0,0.15);">
                    <strong>🤖 Travel Buddy:</strong><br>{format_ai_response(message)}
                </div>
            </div>
            """