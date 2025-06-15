import streamlit as st
from utils.helpers import format_ai_response
from handlers.chat_handler import handle_follow_up_question
from utils.session_state import reset_conversation_history

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
                            <div style="background: aliceblue;
                            color: #000; padding: 12px 16px; border-radius: 18px 18px 5px 18px; 
                                        max-width: 70%; box-shadow: 0 2px 8px rgba(0,0,0,0.15);">
                                <strong>You:</strong><br>{msg['content']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="display: flex; justify-content: flex-start; margin: 10px 0;">
                            <div style="background: darkturquoise;
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

def render_chat_interface(services):
    """Render the complete chat interface"""
    if not st.session_state.search_results:
        st.info("🔍 Search for a location first to start chatting about travel recommendations!")
        return
    
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
                clear_btn_clicked = st.form_submit_button("🗑️ Clear Chat")
                if clear_btn_clicked:
                    reset_conversation_history()
                    st.rerun()
    
    # Handle form submission
    if submit_button and follow_up_question.strip() and not st.session_state.processing_question:
        st.session_state.processing_question = True
        with st.spinner("🤔 Thinking..."):
            response = handle_follow_up_question(
                follow_up_question.strip(), 
                st.session_state.search_results, 
                services
            )
        st.session_state.processing_question = False
        if response:
            st.rerun()
    
    # Show processing status
    if st.session_state.processing_question:
        st.info("🔄 Processing your question... Please wait.")