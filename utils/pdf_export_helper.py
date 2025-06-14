import streamlit as st
import time
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import io
from datetime import datetime
import re

def create_pdf_report(search_results, conversation_history=None):
    """Create a PDF report with travel recommendations and optional chat history"""
    # Ensure conversation_history is a list
    if conversation_history is None:
        conversation_history = []
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, 
                           topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles (keep all your existing styles here)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2E86AB')
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=20,
        textColor=colors.HexColor('#A23B72')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        alignment=TA_JUSTIFY
    )
    
    # Enhanced chat styles with better visual separation
    chat_user_style = ParagraphStyle(
        'ChatUser',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        spaceBefore=8,
        leftIndent=20,
        rightIndent=20,
        textColor=colors.HexColor('#2C5F2D'),
        backColor=colors.HexColor('#F0F8F0'),  # Light green background
        borderColor=colors.HexColor('#2C5F2D'),
        borderWidth=1,
        borderPadding=8,
        borderRadius=5
    )
    
    chat_ai_style = ParagraphStyle(
        'ChatAI',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        spaceBefore=8,
        leftIndent=20,
        rightIndent=20,
        textColor=colors.HexColor('#97233F'),
        backColor=colors.HexColor('#FFF0F3'),  # Light pink background
        borderColor=colors.HexColor('#97233F'),
        borderWidth=1,
        borderPadding=8,
        borderRadius=5
    )
    
    # Style for conversation metadata (timestamps, etc.)
    chat_meta_style = ParagraphStyle(
        'ChatMeta',
        parent=styles['Normal'],
        fontSize=8,
        spaceAfter=3,
        leftIndent=25,
        textColor=colors.HexColor('#666666'),
        fontName='Helvetica-Oblique'
    )
    
    # Style for conversation section divider
    divider_style = ParagraphStyle(
        'Divider',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=10,
        spaceBefore=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#888888')
    )
    
    # Title
    title = Paragraph("🧳 Travel Buddy Recommendations", title_style)
    elements.append(title)
    
    # Generated date
    date_str = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    date_para = Paragraph(f"Generated on {date_str}", styles['Normal'])
    elements.append(date_para)
    elements.append(Spacer(1, 20))
    
    # Location and search type
    location_info = Paragraph(f"<b>Location:</b> {search_results['location']}", normal_style)
    elements.append(location_info)
    
    query_type_map = {
        "tourist_places": "Tourist Places",
        "restaurants": "Restaurants",
        "activities": "Activities",
        "hotels": "Hotels & Resorts"
    }
    query_display = query_type_map.get(search_results['query_type'], search_results['query_type'])
    query_info = Paragraph(f"<b>Search Type:</b> {query_display}", normal_style)
    elements.append(query_info)
    elements.append(Spacer(1, 20))
    
    # AI Recommendations
    rec_title = Paragraph("🤖 AI Travel Recommendations", subtitle_style)
    elements.append(rec_title)
    
    # Clean and format AI response
    cleaned_response = clean_text_for_pdf(search_results['ai_response'])
    
    # Split response into paragraphs and format
    paragraphs = cleaned_response.split('\n\n')
    for para in paragraphs:
        if para.strip():
            # Handle numbered lists
            if re.match(r'^\d+\.', para.strip()):
                para_obj = Paragraph(para.strip(), normal_style)
            else:
                para_obj = Paragraph(para.strip(), normal_style)
            elements.append(para_obj)
    
    elements.append(Spacer(1, 20))
    
    # Places Details Table
    if search_results.get('places_data'):
        places_title = Paragraph("📊 Detailed Place Information", subtitle_style)
        elements.append(places_title)
        
        # Create table data
        table_data = [['Name', 'Rating', 'Price Level', 'Address']]
        
        for place in search_results['places_data'][:10]:  # Limit to first 10 places
            name = place.get('name', 'N/A')[:30]  # Truncate long names
            rating = str(place.get('rating', 'N/A'))
            price_level = '💰' * place.get('price_level', 0) if place.get('price_level') else 'N/A'
            address = place.get('vicinity', place.get('formatted_address', 'N/A'))[:40]
            
            table_data.append([name, rating, price_level, address])
        
        # Create table
        table = Table(table_data, colWidths=[2.2*inch, 0.8*inch, 1*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
    
    # Enhanced Chat History Section - ONLY if there's meaningful conversation
    if conversation_history and len(conversation_history) > 2:
        elements.append(PageBreak())
        chat_title = Paragraph("💬 Your Travel Conversation", subtitle_style)
        elements.append(chat_title)
        
        # Add conversation summary
        summary_text = f"This section contains your personalized travel conversation with {len(conversation_history)} total messages."
        summary_para = Paragraph(summary_text, normal_style)
        elements.append(summary_para)
        elements.append(Spacer(1, 15))
        
        # Skip initial search messages, show only follow-up conversations
        follow_up_messages = conversation_history[2:] if len(conversation_history) > 2 else []
        
        # Remove duplicates and clean messages
        seen_messages = set()
        unique_messages = []
        for msg in follow_up_messages:
            msg_content = msg.get('content', '').strip()
            msg_hash = hash(msg_content.lower()[:100])  # Use hash of first 100 chars
            if msg_content and msg_hash not in seen_messages:
                seen_messages.add(msg_hash)
                unique_messages.append(msg)
        
        # Show conversation with better formatting
        conversation_count = 0
        for i, msg in enumerate(unique_messages[-15:], 1):  # Show last 15 messages
            conversation_count += 1
            
            # Add conversation number for longer conversations
            if conversation_count == 1 and len(unique_messages) > 5:
                divider = Paragraph(f"─── Conversation Messages ───", divider_style)
                elements.append(divider)
            
            if msg['role'] == 'user':
                # User message with icon and formatting
                cleaned_content = clean_text_for_pdf(msg['content'])
                if len(cleaned_content) > 500:
                    cleaned_content = cleaned_content[:500] + "..."
                
                user_text = f"<b>👤 You:</b><br/>{cleaned_content}"
                user_para = Paragraph(user_text, chat_user_style)
                elements.append(user_para)
                
            else:
                # AI message with icon and formatting
                cleaned_content = clean_text_for_pdf(msg['content'])
                if len(cleaned_content) > 800:
                    cleaned_content = cleaned_content[:800] + "..."
                
                ai_text = f"<b>🤖 Travel Buddy:</b><br/>{cleaned_content}"
                ai_para = Paragraph(ai_text, chat_ai_style)
                elements.append(ai_para)
            
            # Add small spacer between messages
            elements.append(Spacer(1, 5))
            
            # Add section break every 5 messages for readability
            if conversation_count % 5 == 0 and conversation_count < len(unique_messages[-15:]):
                section_break = Paragraph("• • •", divider_style)
                elements.append(section_break)
        
        # Add conversation statistics
        elements.append(Spacer(1, 20))
    
    elif conversation_history and len(conversation_history) <= 2:
        # Add a note when there's only initial search without follow-up conversation
        elements.append(Spacer(1, 20))
        no_chat_note = Paragraph("💡 <i>No follow-up conversation yet. Start chatting to include your questions and AI responses in future reports!</i>", 
                                ParagraphStyle('NoChat', parent=styles['Normal'], fontSize=10, 
                                             alignment=TA_CENTER, textColor=colors.HexColor('#666666')))
        elements.append(no_chat_note)
    
    # Enhanced Footer
    elements.append(Spacer(1, 30))
    footer_line = Paragraph("─" * 60, ParagraphStyle('FooterLine', parent=styles['Normal'], 
                           fontSize=8, alignment=TA_CENTER, textColor=colors.grey))
    elements.append(footer_line)
    
    footer = Paragraph("Built with ❤️ by Traveller Vishwa - Travel Buddy App<br/>Your Personal AI Travel Companion", 
                      ParagraphStyle('Footer', parent=styles['Normal'], 
                                   fontSize=8, alignment=TA_CENTER, 
                                   textColor=colors.grey, spaceAfter=5))
    elements.append(footer)
    
    # Build PDF
    try:
        doc.build(elements)
    except Exception as e:
        # Log the error and create a simple fallback PDF
        logging.error(f"Error building PDF: {str(e)}")
        # Create a minimal PDF as fallback
        elements = [
            Paragraph("Travel Buddy Report", title_style),
            Paragraph(f"Location: {search_results.get('location', 'Unknown')}", normal_style),
            Paragraph("An error occurred while generating the full report.", normal_style),
            Paragraph("Please try again or contact support.", normal_style)
        ]
        doc.build(elements)
    
    buffer.seek(0)
    return buffer

def clean_text_for_pdf(text):
    """Enhanced text cleaning function for better PDF formatting"""
    if not text:
        return ""
    
    # Remove or replace problematic characters
    text = text.replace('\u2019', "'")  # Right single quotation mark
    text = text.replace('\u2018', "'")  # Left single quotation mark
    text = text.replace('\u201c', '"')  # Left double quotation mark
    text = text.replace('\u201d', '"')  # Right double quotation mark
    text = text.replace('\u2013', '-')  # En dash
    text = text.replace('\u2014', '--') # Em dash
    text = text.replace('\u2026', '...') # Horizontal ellipsis
    
    # Clean up excessive whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double newline
    text = re.sub(r' +', ' ', text)  # Multiple spaces to single space
    text = text.strip()
    
    # Handle HTML-like tags that might be in the text
    text = re.sub(r'<[^>]+>', '', text)
    
    # Escape XML/HTML characters for ReportLab
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    
    return text
