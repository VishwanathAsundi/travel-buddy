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
            
            if follow_up_messages:
                st.markdown("### 💭 Your Conversation History")
                
                # Display messages in a clean chat format
                for i, msg in enumerate(follow_up_messages[-8:]):  # Show last 8 follow-up messages
                    if msg['role'] == 'user':
                        st.markdown(f"""
                        <div style="display: flex; justify-content: flex-end; margin: 10px 0;">
                            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                        color: white; padding: 12px 16px; border-radius: 18px 18px 5px 18px; 
                                        max-width: 70%; box-shadow: 0 2px 8px rgba(0,0,0,0.15);">
                                <strong>You:</strong><br>{msg['content']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="display: flex; justify-content: flex-start; margin: 10px 0;">
                            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                                        color: white; padding: 12px 16px; border-radius: 18px 18px 18px 5px; 
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
    """Handle follow-up questions with proper error handling"""
    try:
        # Initialize conversation history if needed
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []
        
        # Check if this exact question was just asked to prevent duplicates
        if (st.session_state.conversation_history and 
            len(st.session_state.conversation_history) > 0 and
            st.session_state.conversation_history[-2:] and
            any(msg.get('content') == question and msg.get('role') == 'user' 
                for msg in st.session_state.conversation_history[-2:])):
            return st.session_state.conversation_history[-1]['content']
        
        # Get context and generate response
        context_history = services['context'].get_context_messages()
        
        ai_response = services['openai'].generate_travel_recommendations(
            search_results['places_data'],
            search_results['query_type'],
            question,
            context_history
        )
        
        # Add both user question and AI response to conversation history
        current_time = st.session_state.get('message_counter', 0)
        
        st.session_state.conversation_history.extend([
            {
                'role': 'user',
                'content': question,
                'timestamp': current_time
            },
            {
                'role': 'assistant',
                'content': ai_response,
                'timestamp': current_time + 1
            }
        ])
        
        # Update context manager
        services['context'].add_message("user", question)
        services['context'].add_message("assistant", ai_response)
        
        # Increment message counter
        st.session_state.message_counter = current_time + 2
        
        return ai_response
        
    except Exception as e:
        logging.error(f"Error handling follow-up question: {str(e)}")
        error_msg = f"Sorry, I encountered an error while processing your question: {str(e)}"
        
        # Add error to conversation history
        st.session_state.conversation_history.append({
            'role': 'assistant',
            'content': error_msg,
            'timestamp': st.session_state.get('message_counter', 0) + 1
        })
        
        return error_msg

def handle_quick_question(question_key, question_text, search_results):
    """Handle quick question buttons with duplicate prevention"""
    # Use session state to track if this question was just processed
    question_state_key = f"processed_{question_key}"
    
    if st.session_state.get(question_state_key, False):
        # Reset the flag and don't process again
        st.session_state[question_state_key] = False
        return
    
    # Set the flag to prevent immediate reprocessing
    st.session_state[question_state_key] = True
    
    # Process the question
    with st.spinner("🤔 Thinking..."):
        handle_follow_up_question(question_text, search_results)

def main():
    # Initialize session state variables
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []

    if 'last_search' not in st.session_state:
        st.session_state.last_search = None

    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    
    if 'message_counter' not in st.session_state:
        st.session_state.message_counter = 0

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
            # Keep initial search results but clear follow-up conversations
            if len(st.session_state.conversation_history) > 2:
                st.session_state.conversation_history = st.session_state.conversation_history[:2]
            else:
                st.session_state.conversation_history = []
            st.session_state.message_counter = 2 if st.session_state.search_results else 0
            services['context'].clear_history()
            
            # Clear quick question flags
            for key in list(st.session_state.keys()):
                if key.startswith('processed_'):
                    del st.session_state[key]
            
            st.success("Chat history cleared!")
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
                
                # Add to conversation history
                st.session_state.conversation_history.append({
                    'role': 'user',
                    'content': user_query,
                    'timestamp': st.session_state.get('message_counter', 0)
                })
                st.session_state.conversation_history.append({
                    'role': 'assistant',
                    'content': ai_response,
                    'timestamp': st.session_state.get('message_counter', 0) + 1
                })
                st.session_state.message_counter = st.session_state.get('message_counter', 0) + 2
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
                nearby_names = [place.get('name', 'Unknown') for place in nearby_places[:5]]
                st.write("Consider visiting these nearby locations: " + ", ".join(nearby_names))
    
    # Chat interface for follow-up questions - FIXED SECTION
    if st.session_state.search_results:
        st.markdown("---")
        
        # Display integrated chat interface
        display_chat_interface()
        
        # Input section at the bottom
        st.markdown("### 💭 Ask a Question")
        
        # Create columns for better layout
        col1, col2 = st.columns([4, 1])
        
        with col1:
            # Use a form to handle the input properly
            with st.form(key="chat_form", clear_on_submit=True):
                follow_up_question = st.text_input(
                    "Ask a follow-up question",
                    placeholder="Ask about timing, budget, alternatives, or anything else...",
                    label_visibility="collapsed"
                )

                
                # Create two columns for buttons
                btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])
                
                with btn_col1:
                    submit_button = st.form_submit_button("💬 Send", type="primary")
                
                with btn_col2:
                    if st.form_submit_button("🗑️ Clear Chat"):
                        # Clear only follow-up conversation, keep initial search
                        if len(st.session_state.conversation_history) > 2:
                            st.session_state.conversation_history = st.session_state.conversation_history[:2]
                        st.rerun()
        
        with col2:
            # Quick question suggestions - FIXED
            st.markdown("**💡 Quick Questions:**")
            
            # Best times question
            if st.button("🕒 Best times to visit?", key="time_btn"):
                handle_quick_question(
                    "time_btn", 
                    "What are the best times to visit these places?", 
                    st.session_state.search_results
                )
                st.rerun()
            
            # Budget question  
            if st.button("💰 Budget options?", key="budget_btn"):
                handle_quick_question(
                    "budget_btn",
                    "What are some budget-friendly options among these places?", 
                    st.session_state.search_results
                )
                st.rerun()
            
            # Transportation question
            if st.button("🚗 How to get there?", key="transport_btn"):
                handle_quick_question(
                    "transport_btn",
                    "How can I get to these places? What are the transportation options?", 
                    st.session_state.search_results
                )
                st.rerun()
        
        # Handle form submission
        if submit_button and follow_up_question.strip():
            with st.spinner("🤔 Thinking..."):
                handle_follow_up_question(follow_up_question.strip(), st.session_state.search_results)
            st.rerun()
    
    else:
        st.info("🔍 Search for a location first to start chatting about travel recommendations!")

    # Footer
    st.markdown("---")
    st.markdown("*Built with ❤️ using Streamlit, Azure OpenAI, and Google Places API*")

if __name__ == "__main__":
    main()