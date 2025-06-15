import streamlit as st
import logging
import time

def handle_follow_up_question(question, search_results, services):
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
                'timestamp': int(time.time() * 1000),
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