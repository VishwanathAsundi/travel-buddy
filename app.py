import streamlit as st
import logging
from services.azure_openai_service import AzureOpenAIService
from services.google_places_service import GooglePlacesService
from services.context_manager import ContextManager
from ui.sidebar import render_sidebar
from ui.main_content import render_main_content
from ui.chat_interface import render_chat_interface
from utils.session_state import initialize_session_state
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)

# Page configuration
st.set_page_config(
    page_title="Travel Buddy 🏍️",
    page_icon="🏍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def init_services():
    """Initialize and cache services"""
    return {
        'openai': AzureOpenAIService(),
        'places': GooglePlacesService(),
        'context': ContextManager()
    }

def main():
    # Show loader during initial service initialization
    with st.spinner("Please wait, your travel buddy is getting ready!"):
        services = init_services()

    # Initialize session state
    initialize_session_state()

    # App header
    st.title("🧳 Travel Buddy 🏍️")
    st.markdown("*Your AI-powered travel companion for discovering amazing places, restaurants, activities, and accommodations.*")
    
    # Render sidebar
    search_params = render_sidebar(services)
    
    # Render main content based on search state
    render_main_content(services, search_params)
    
    # Render chat interface if we have search results
    if st.session_state.search_results:
        render_chat_interface(services)
    
    # Footer
    st.markdown("---")
    st.markdown("*Built with ❤️ by Traveller Vishwa*")

if __name__ == "__main__":
    main()