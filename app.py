import streamlit as st
import logging
from services.azure_openai_service import AzureOpenAIService
from services.google_places_service import GooglePlacesService
from services.context_manager import ContextManager
from utils.helpers import display_places_data, create_summary_card, format_ai_response, get_distance_options
from config import Config
import time

# Configure logging
logging.basicConfig(level=logging.INFO)

# Page configuration
st.set_page_config(
    page_title="Travel Buddy 🏍️",
    page_icon="🏍️",
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

def display_chat_interface():
    """Display an integrated chat interface with conversation history"""
    st.header("💬 Chat with Travel Buddy")
    
    # Create chat container with custom styling
    chat_container = st.container()
    
    with chat_container:
        if 'conversation_history' in st.session_state and st.session_state.conversation_history:
            # Filter out the initial search queries to avoid duplication
            # Only show follow-up conversations (skip first 2 messages which are initial search)
            follow_up_messages = []
            if len(st.session_state.conversation_history) > 2:
                follow_up_messages = st.session_state.conversation_history[2:]

            # Remove duplicate messages from the follow_up_messages
            seen_messages = set()
            unique_follow_up_messages = []
            for msg in follow_up_messages:
                msg_content = msg.get('content', '').strip().lower()
                if msg_content and msg_content not in seen_messages:
                    seen_messages.add(msg_content)
                    unique_follow_up_messages.append(msg)

            if unique_follow_up_messages:
                
                # Display messages in a clean chat format
                for i, msg in enumerate(unique_follow_up_messages[-10:]):  # Show last 10 follow-up messages
                    if msg['role'] == 'user':
                        st.markdown(f"""
                        <div style="display: flex; justify-content: flex-end; margin: 10px 0;">
                            <div style="background: #ccc;
                            color: #000; padding: 12px 16px; border-radius: 18px 18px 5px 18px; 
                                        max-width: 70%; box-shadow: 0 2px 8px rgba(0,0,0,0.15);">
                                <strong>You:</strong><br>{msg['content']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="display: flex; justify-content: flex-start; margin: 10px 0;">
                            <div style="background: rgb(221, 148, 148);
                                        color: #000; padding: 12px 16px; border-radius: 18px 18px 18px 5px; 
                                        max-width: 70%; box-shadow: 0 2px 8px rgba(0,0,0,0.15);">
                                <strong>🤖 Travel Buddy:</strong><br>{format_ai_response(msg['content'])}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("💡 Start a conversation! Ask any follow-up questions about your travel plans.")
        else:
            st.info("💡 No conversation yet. Ask your first question about the places you're exploring!")

def handle_follow_up_question(question, search_results):
    """Handle follow-up questions with proper error handling and duplicate prevention"""
    try:
        # Initialize conversation history if needed
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []
        
        # Check if this exact question was just asked to prevent duplicates
        if (st.session_state.conversation_history and 
            len(st.session_state.conversation_history) >= 2):
            # Check the last user message
            last_messages = st.session_state.conversation_history[-2:]
            for msg in last_messages:
                if (msg.get('role') == 'user' and 
                    msg.get('content', '').strip().lower() == question.strip().lower()):
                    # Question already exists, don't add duplicate
                    logging.info(f"Duplicate question detected, skipping: {question}")
                    return None
        
        # Get context and generate response
        context_history = services['context'].get_context_messages()
        
        ai_response = services['openai'].generate_travel_recommendations(
            search_results['places_data'],
            search_results['query_type'],
            question,
            context_history
        )
        
        # Add both user question and AI response to conversation history
        st.session_state.conversation_history.extend([
            {
                'role': 'user',
                'content': question,
                'timestamp': int(time.time() * 1000),
                'id': f"user_{int(time.time() * 1000)}"
            },
            {
                'role': 'assistant',
                'content': ai_response,
                'timestamp': int(time.time() * 1000) + 1,
                'id': f"assistant_{int(time.time() * 1000)}"
            }
        ])
        
        # Update context manager
        services['context'].add_message("user", question)
        services['context'].add_message("assistant", ai_response)
        
        return ai_response
        
    except Exception as e:
        logging.error(f"Error handling follow-up question: {str(e)}")
        error_msg = f"Sorry, I encountered an error while processing your question: {str(e)}"
        
        # Add error to conversation history
        error_time = int(time.time() * 1000)
        st.session_state.conversation_history.append({
            'role': 'assistant',
            'content': error_msg,
            'timestamp': error_time,
            'id': f"error_{error_time}"
        })
        
        return error_msg

def main():
    # Initialize session state variables
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []

    if 'last_search' not in st.session_state:
        st.session_state.last_search = None

    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    
    if 'processing_question' not in st.session_state:
        st.session_state.processing_question = False

    st.title("🧳 Travel Buddy 🏍️")
    st.markdown("*Your AI-powered travel companion for discovering amazing places, restaurants, activities, and accommodations.*")
    
    # Sidebar
    with st.sidebar:
        st.header("🎯 Search Options")
        
        # Location input
        location = st.text_input("📍 Enter Location", placeholder="e.g., Gokarna, Goa, Italy")
        
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
            # Keep initial search results but clear follow-up conversations
            if len(st.session_state.conversation_history) > 2:
                st.session_state.conversation_history = st.session_state.conversation_history[:2]
            else:
                st.session_state.conversation_history = []
            services['context'].clear_history()
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
    
    # Handle search
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
            else:
                st.error(f"No {selected_query_type.lower()} found in {location}. Try a different location or search type.")
    
    # Display results
    if st.session_state.search_results:
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
                nearby_names = [place.get('name', 'Unknown') for place in nearby_places[:10]]
                st.write("Consider visiting these nearby locations: " + ", ".join(nearby_names))
    
    # Chat interface for follow-up questions - FIXED SECTION
    if st.session_state.search_results:
        st.markdown("---")
        
        # Display integrated chat interface
        display_chat_interface()
        
        # Input section at the bottom
        st.markdown("### 💭 Ask a Question")
        
        # Use a form to handle the input properly
        with st.form(key="chat_form", clear_on_submit=True):
                follow_up_question = st.text_input(
                    "Ask a follow-up question",
                    placeholder="Ask about timing, budget, alternatives, or anything else...",
                    label_visibility="collapsed",
                    disabled=st.session_state.processing_question
                )
                
               # Create button container
                with st.container():
                    # Create columns: wide left for Send button, right-aligned narrow column for Clear Chat
                    col1, col2 = st.columns([6, 1])

                    with col1:
                        submit_button = st.form_submit_button(
                            "💬 Send",
                            type="primary",
                            disabled=st.session_state.processing_question
                        )

                    with col2:
                        # Right-align Clear Chat button manually using HTML/CSS inside markdown
                        clear_btn_clicked = st.form_submit_button("🗑️ Clear Chat")
                        if clear_btn_clicked:
                            if len(st.session_state.conversation_history) > 2:
                                st.session_state.conversation_history = st.session_state.conversation_history[:2]
                            st.session_state.processing_question = False
                            st.rerun()

        
        # Handle form submission
        if submit_button and follow_up_question.strip() and not st.session_state.processing_question:
            st.session_state.processing_question = True
            with st.spinner("🤔 Thinking..."):
                response = handle_follow_up_question(follow_up_question.strip(), st.session_state.search_results)
            st.session_state.processing_question = False
            if response:
                st.rerun()
        
        # Show processing status
        if st.session_state.processing_question:
            st.info("🔄 Processing your question... Please wait.")
    
    else:
        st.info("🔍 Search for a location first to start chatting about travel recommendations!")

    # Footer
    st.markdown("---")
    st.markdown("*Built with ❤️ by Traveller*")

if __name__ == "__main__":
    main()