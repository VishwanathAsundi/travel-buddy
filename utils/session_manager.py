import streamlit as st
import time

class SessionManager:
    """Manages Streamlit session state variables"""
    
    def __init__(self):
        self.required_session_vars = [
            'conversation_history',
            'last_search',
            'search_results',
            'processing_question'
        ]
    
    def initialize_session_state(self):
        """Initialize all required session state variables"""
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []

        if 'last_search' not in st.session_state:
            st.session_state.last_search = None

        if 'search_results' not in st.session_state:
            st.session_state.search_results = None
        
        if 'processing_question' not in st.session_state:
            st.session_state.processing_question = False
    
    def should_perform_new_search(self, search_params):
        """Check if a new search should be performed"""
        current_search = (search_params['location'], search_params['query_type'])
        return st.session_state.get('last_search') != current_search
    
    def update_search_results(self, location, query_type, places_data, ai_response):
        """Update search results in session state"""
        st.session_state.last_search = (location, query_type)
        st.session_state.search_results = {
            'places_data': places_data,
            'ai_response': ai_response,
            'location': location,
            'query_type': query_type
        }
    
    def clear_conversation_history(self, keep_initial_search=True):
        """Clear conversation history, optionally keeping initial search"""
        if keep_initial_search and len(st.session_state.conversation_history) > 2:
            st.session_state.conversation_history = st.session_state.conversation_history[:2]
        else:
            st.session_state.conversation_history = []
        st.session_state.processing_question = False
    
    def add_conversation_messages(self, messages):
        """Add messages to conversation history"""
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []
        
        st.session_state.conversation_history.extend(messages)
    
    def initialize_conversation_with_search(self, user_query, ai_response):
        """Initialize conversation history with search results"""
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
    
    def get_conversation_stats(self):
        """Get conversation statistics"""
        history_count = len(st.session_state.get('conversation_history', []))
        follow_up_count = max(0, history_count - 2) if history_count > 2 else 0
        return {
            'total_messages': history_count,
            'follow_up_messages': follow_up_count
        }