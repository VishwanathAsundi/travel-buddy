import streamlit as st
import logging
from services.azure_openai_service import AzureOpenAIService
from services.google_places_service import GooglePlacesService
from services.context_manager import ContextManager
from ui.components import UIComponents
from ui.sidebar import SidebarManager
from ui.chat_interface import ChatInterface
from handlers.search_handler import SearchHandler
from handlers.chat_handler import ChatHandler
from utils.session_manager import SessionManager

# Configure logging
logging.basicConfig(level=logging.INFO)

# Page configuration
st.set_page_config(
    page_title="Travel Buddy 🏍️",
    page_icon="🏍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Initialize session manager
    session_manager = SessionManager()
    session_manager.initialize_session_state()
    
    # Show loader during initial service initialization
    with st.spinner("please wait your travel buddy is getting ready!"):
        @st.cache_resource
        def init_services():
            return {
                'openai': AzureOpenAIService(),
                'places': GooglePlacesService(),
                'context': ContextManager()
            }
        services = init_services()

    # Initialize handlers
    search_handler = SearchHandler(services)
    chat_handler = ChatHandler(services)
    
    # Initialize UI components
    ui_components = UIComponents()
    sidebar_manager = SidebarManager()
    chat_interface = ChatInterface()

    # App header
    ui_components.display_app_header()
    
    # Render sidebar and get search parameters
    search_params = sidebar_manager.render_sidebar()
    
    # Main content area
    if not search_params['location']:
        ui_components.display_welcome_screen()
        return
    
    # Handle search
    if search_params['search_clicked'] or session_manager.should_perform_new_search(search_params):
        search_handler.handle_search(search_params)
    
    # Display results
    if st.session_state.search_results:
        ui_components.display_search_results(st.session_state.search_results, search_params['selected_query_type'])
        
        # Display chat interface
        chat_interface.display_chat_interface()
        
        # Handle chat input
        chat_handler.handle_chat_input()
    else:
        st.info("🔍 Search for a location first to start chatting about travel recommendations!")

    # Footer
    ui_components.display_footer()

if __name__ == "__main__":
    main()