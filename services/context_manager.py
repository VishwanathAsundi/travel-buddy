import streamlit as st
from datetime import datetime
import json

class ContextManager:
    def __init__(self):
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []
        if 'user_preferences' not in st.session_state:
            st.session_state.user_preferences = {}
    
    def add_message(self, role, content, metadata=None):
        """Add a message to conversation history"""
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        st.session_state.conversation_history.append(message)
        
        # Keep only recent messages to manage memory
        if len(st.session_state.conversation_history) > 20:
            st.session_state.conversation_history = st.session_state.conversation_history[-20:]
    
    def get_context_messages(self):
        """Get formatted messages for AI context"""
        return [
            {"role": msg['role'], "content": msg['content']} 
            for msg in st.session_state.conversation_history[-10:]
        ]
    
    def save_user_preference(self, key, value):
        """Save user preference"""
        st.session_state.user_preferences[key] = value
    
    def get_user_preference(self, key, default=None):
        """Get user preference"""
        return st.session_state.user_preferences.get(key, default)
    
    def clear_history(self):
        """Clear conversation history"""
        st.session_state.conversation_history = []
    
    def export_history(self):
        """Export conversation history as JSON"""
        return json.dumps(st.session_state.conversation_history, indent=2)