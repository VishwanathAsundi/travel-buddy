import streamlit as st
import logging
import time
from ui.chat_interface import ChatInterface
from utils.session_manager import SessionManager

class ChatHandler:
    """Handles chat operations and follow-up questions"""
    
    def __init__(self, services):
        self.services = services
        self.chat_interface = ChatInterface()
        self.session_manager = SessionManager()
    
    def handle_chat_input(self):
        """Handle chat input form and process questions"""
        # Render chat input form
        form_data = self.chat_interface.render_chat_input_form()
        
        # Handle clear chat button
        if form_data['clear_clicked']:
            self._handle_clear_chat()
            return
        
        # Handle question submission
        if (form_data['submit_clicked'] and 
            form_data['question'].strip() and 
            not st.session_state.processing_question):
            
            self._handle_follow_up_question(form_data['question'].strip())
        
        # Show processing status
        if st.session_state.processing_question:
            st.info("🔄 Processing your question... Please wait.")
    
    def _handle_follow_up_question(self, question):
        """Handle follow-up questions with proper error handling and duplicate prevention"""
        try:
            # Check for duplicate questions
            if self._is_duplicate_question(question):
                logging.info(f"Duplicate question detected, skipping: {question}")
                return
            
            # Set processing state
            st.session_state.processing_question = True
            
            with st.spinner("🤔 Thinking..."):
                # Generate AI response
                ai_response = self._generate_ai_response(question)
                
                # Add messages to conversation history
                self._add_conversation_messages(question, ai_response)
                
                # Update context manager
                self.services['context'].add_message("user", question)
                self.services['context'].add_message("assistant", ai_response)
            
            # Reset processing state and refresh
            st.session_state.processing_question = False
            st.rerun()
            
        except Exception as e:
            logging.error(f"Error handling follow-up question: {str(e)}")
            error_msg = f"Sorry, I encountered an error while processing your question: {str(e)}"
            
            # Add error to conversation history
            self._add_error_message(error_msg)
            st.session_state.processing_question = False
    
    def _is_duplicate_question(self, question):
        """Check if the question is a duplicate of recent messages"""
        if (st.session_state.conversation_history and 
            len(st.session_state.conversation_history) >= 2):
            
            # Check the last few user messages
            last_messages = st.session_state.conversation_history[-4:]  # Check last 4 messages
            for msg in last_messages:
                if (msg.get('role') == 'user' and 
                    msg.get('content', '').strip().lower() == question.strip().lower()):
                    return True
        return False
    
    def _generate_ai_response(self, question):
        """Generate AI response for the follow-up question"""
        search_results = st.session_state.search_results
        context_history = self.services['context'].get_context_messages()
        
        return self.services['openai'].generate_travel_recommendations(
            search_results['places_data'],
            search_results['query_type'],
            question,
            context_history
        )
    
    def _add_conversation_messages(self, question, ai_response):
        """Add question and response to conversation history"""
        current_time = int(time.time() * 1000)
        
        messages = [
            {
                'role': 'user',
                'content': question,
                'timestamp': current_time,
                'id': f"user_{current_time}"
            },
            {
                'role': 'assistant',
                'content': ai_response,
                'timestamp': current_time + 1,
                'id': f"assistant_{current_time}"
            }
        ]
        
        self.session_manager.add_conversation_messages(messages)
    
    def _add_error_message(self, error_msg):
        """Add error message to conversation history"""
        error_time = int(time.time() * 1000)
        error_message = {
            'role': 'assistant',
            'content': error_msg,
            'timestamp': error_time,
            'id': f"error_{error_time}"
        }
        
        self.session_manager.add_conversation_messages([error_message])
    
    def _handle_clear_chat(self):
        """Handle clearing chat history"""
        self.session_manager.clear_conversation_history(keep_initial_search=True)
        self.services['context'].clear_history()
        st.success("Chat history cleared!")
        st.rerun()