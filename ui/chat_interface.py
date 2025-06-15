import streamlit as st
from ui.components import UIComponents

class ChatInterface:
    """Manages the chat interface display and interactions"""
    
    def __init__(self):
        self.ui_components = UIComponents()
    
    def display_chat_interface(self):
        """Display the integrated chat interface with conversation history"""
        st.markdown("---")
        st.header("💬 Chat with Travel Buddy")
        
        # Create chat container with custom styling
        chat_container = st.container()
        
        with chat_container:
            if 'conversation_history' in st.session_state and st.session_state.conversation_history:
                self._display_conversation_history()
            else:
                st.info("💡 No conversation yet. Ask your first question about the places you're exploring!")
    
    def _display_conversation_history(self):
        """Display the conversation history in chat format"""
        # Filter out the initial search queries to avoid duplication
        follow_up_messages = self._get_follow_up_messages()
        
        if follow_up_messages:
            # Display messages in a clean chat format
            for msg in follow_up_messages[-10:]:  # Show last 10 follow-up messages
                if msg['role'] == 'user':
                    html_content = self.ui_components.create_chat_message_html(msg['content'], is_user=True)
                else:
                    html_content = self.ui_components.create_chat_message_html(msg['content'], is_user=False)
                
                st.markdown(html_content, unsafe_allow_html=True)
        else:
            st.info("💡 Start a conversation! Ask any follow-up questions about your travel plans.")
    
    def _get_follow_up_messages(self):
        """Get unique follow-up messages from conversation history"""
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
        
        return unique_follow_up_messages
    
    def render_chat_input_form(self):
        """Render the chat input form and return form data"""
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
                    clear_btn_clicked = st.form_submit_button("🗑️ Clear Chat")
        
        return {
            'question': follow_up_question,
            'submit_clicked': submit_button,
            'clear_clicked': clear_btn_clicked
        }