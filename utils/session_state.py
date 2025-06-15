import streamlit as st

def initialize_session_state():
    """Initialize all session state variables"""
    session_defaults = {
        'conversation_history': [],
        'last_search': None,
        'search_results': None,
        'processing_question': False,
        'current_location': None,
        'getLocation()': None
    }
    
    for key, default_value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def reset_conversation_history():
    """Reset conversation history while keeping initial search results"""
    if len(st.session_state.conversation_history) > 2:
        st.session_state.conversation_history = st.session_state.conversation_history[:2]
    else:
        st.session_state.conversation_history = []
    st.session_state.processing_question = False

def clear_search_results():
    """Clear all search results and conversation history"""
    st.session_state.search_results = None
    st.session_state.last_search = None
    st.session_state.conversation_history = []
    st.session_state.processing_question = False