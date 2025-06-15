import streamlit as st
from utils.helpers import display_places_data, format_ai_response

class UIComponents:
    """Reusable UI components for the Travel Buddy app"""
    
    def display_app_header(self):
        """Display the app header"""
        st.title("🧳 Travel Buddy 🏍️")
        st.markdown("*Your AI-powered travel companion for discovering amazing places, restaurants, activities, and accommodations worldwide.*")

    def display_welcome_screen(self):
        """Display a modern welcome screen using cards with a clean, elegant UI"""

        st.markdown("""
            <style>
                .card {
                    background-color: #f9f9f9;
                    border-radius: 16px;
                    padding: 20px;
                    margin-bottom: 20px;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                    transition: transform 0.2s ease;
                    border-left: 2px solid #ccc;
                }
                .card h4 {
                    margin-top: 0;
                    color: #2c3e50;
                }
                .card ul {
                    padding-left: 20px;
                }
                .info-box {
                    background-color: #eaf4ff;
                    padding: 15px 20px;
                    border-left: 5px solid #3399ff;
                    border-radius: 8px;
                    margin-bottom: 30px;
                    color: #2c3e50;
                }
            </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="info-box">👈 <strong>Please enter a location in the sidebar to get started!</strong></div>', unsafe_allow_html=True)

        st.subheader("🌟 What Travel Buddy can help you with:")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
                <div class="card">
                    <h4>🏛️ Tourist Places</h4>
                    <ul>
                        <li>Top attractions and landmarks</li>
                        <li>Hidden gems and local favorites</li>
                        <li>Cultural and historical sites</li>
                        <li>Best visiting times</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("""
                <div class="card">
                    <h4>🍽️ Restaurants</h4>
                    <ul>
                        <li>Local cuisine recommendations</li>
                        <li>Price ranges and cost estimates</li>
                        <li>Popular dishes to try</li>
                        <li>Restaurant ratings and reviews</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
                <div class="card">
                    <h4>🎯 Activities</h4>
                    <ul>
                        <li>Adventure and outdoor activities</li>
                        <li>Cultural experiences</li>
                        <li>Entertainment options</li>
                        <li>Seasonal recommendations</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("""
                <div class="card">
                    <h4>🏨 Hotels & Resorts</h4>
                    <ul>
                        <li>Accommodation options</li>
                        <li>Price ranges per night</li>
                        <li>Amenities and features</li>
                        <li>Location advantages</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)

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
        st.markdown("*Built with ❤️ by a Traveller for Travellers*")
    
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