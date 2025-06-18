import streamlit as st
import time
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.graphics.shapes import Drawing, Rect, Line
from reportlab.graphics import renderPDF
import io
from datetime import datetime
import re
import logging

def create_beautiful_header_line(width=6*inch, color='#2E86AB'):
    """Create a decorative header line"""
    drawing = Drawing(width, 10)
    drawing.add(Line(0, 5, width, 5, strokeColor=colors.HexColor(color), strokeWidth=2))
    return drawing

def create_section_divider(width=6*inch, color='#E8E8E8'):
    """Create a subtle section divider"""
    drawing = Drawing(width, 15)
    drawing.add(Line(width*0.25, 7, width*0.75, 7, strokeColor=colors.HexColor(color), strokeWidth=1))
    return drawing

def create_pdf_report(search_results, conversation_history=None):
    """Create a beautifully formatted PDF report with travel recommendations and chat history"""
    if conversation_history is None:
        conversation_history = []
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=50, 
        leftMargin=50, 
        topMargin=60, 
        bottomMargin=50
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Enhanced Custom Styles
    title_style = ParagraphStyle(
        'BeautifulTitle',
        parent=styles['Heading1'],
        fontSize=28,
        spaceAfter=20,
        spaceBefore=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1A365D'),
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'BeautifulSubtitle',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=15,
        spaceBefore=20,
        textColor=colors.HexColor('#2D3748'),
        fontName='Helvetica-Bold',
        borderPadding=5
    )
    
    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading3'],
        fontSize=16,
        spaceAfter=12,
        spaceBefore=15,
        textColor=colors.HexColor('#2B6CB0'),
        fontName='Helvetica-Bold',
        leftIndent=0
    )
    
    place_title_style = ParagraphStyle(
        'PlaceTitle',
        parent=styles['Normal'],
        fontSize=14,
        spaceAfter=8,
        spaceBefore=12,
        textColor=colors.HexColor('#1A202C'),
        fontName='Helvetica-Bold',
        backColor=colors.HexColor('#F7FAFC'),
        borderColor=colors.HexColor('#E2E8F0'),
        borderWidth=1,
        borderPadding=8,
        borderRadius=3
    )
    
    place_detail_style = ParagraphStyle(
        'PlaceDetail',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        leftIndent=15,
        rightIndent=15,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#2D3748'),
        leading=14
    )
    
    info_box_style = ParagraphStyle(
        'InfoBox',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=8,
        leftIndent=20,
        rightIndent=20,
        backColor=colors.HexColor('#EBF8FF'),
        borderColor=colors.HexColor('#3182CE'),
        borderWidth=1,
        borderPadding=10,
        borderRadius=5,
        textColor=colors.HexColor('#2A4365')
    )
    
    # Enhanced Chat Styles
    chat_user_style = ParagraphStyle(
        'ChatUserBeautiful',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=10,
        spaceBefore=8,
        leftIndent=30,
        rightIndent=80,
        backColor=colors.HexColor('#F0FFF4'),
        borderColor=colors.HexColor('#38A169'),
        borderWidth=1,
        borderPadding=12,
        borderRadius=8,
        textColor=colors.HexColor('#1A202C')
    )
    
    chat_ai_style = ParagraphStyle(
        'ChatAIBeautiful',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=10,
        spaceBefore=8,
        leftIndent=80,
        rightIndent=30,
        backColor=colors.HexColor('#FFF5F5'),
        borderColor=colors.HexColor('#E53E3E'),
        borderWidth=1,
        borderPadding=12,
        borderRadius=8,
        textColor=colors.HexColor('#1A202C')
    )
    
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=5,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#718096'),
        fontName='Helvetica-Oblique'
    )
    
    # Beautiful Header Section
    elements.append(create_beautiful_header_line())
    elements.append(Spacer(1, 10))
    
    # Main Title with Icon
    title = Paragraph("🌟 Travel Buddy Recommendations", title_style)
    elements.append(title)
    
    # Subtitle with date
    date_str = datetime.now().strftime("%B %d, %Y")
    subtitle = Paragraph(f"Your Personalized Travel Guide • {date_str}", meta_style)
    elements.append(subtitle)
    
    elements.append(Spacer(1, 15))
    elements.append(create_beautiful_header_line())
    elements.append(Spacer(1, 25))
    
    # Trip Information Box
    query_type_map = {
        "tourist_places": "🏛️ Tourist Places & Attractions",
        "restaurants": "🍽️ Restaurants & Dining",
        "activities": "🎯 Activities & Adventures", 
        "hotels": "🏨 Hotels & Accommodations"
    }
    query_display = query_type_map.get(search_results['query_type'], search_results['query_type'])
    
    trip_info = f"""
    📍 <b>Destination:</b> {search_results['location']}<br/>
    🔍 <b>Search Focus:</b> {query_display}<br/>
    📅 <b>Report Generated:</b> {datetime.now().strftime("%I:%M %p, %B %d, %Y")}
    """
    
    info_box = Paragraph(trip_info, info_box_style)
    elements.append(info_box)
    elements.append(Spacer(1, 25))
    
    # AI Recommendations Section
    rec_section = Paragraph("🤖 Your AI Travel Recommendations", subtitle_style)
    elements.append(rec_section)
    elements.append(create_section_divider())
    elements.append(Spacer(1, 15))
    
    # Parse and beautifully format AI response
    ai_response = search_results.get('ai_response', '')
    formatted_recommendations = format_ai_recommendations(ai_response, place_title_style, place_detail_style, info_box_style)
    
    for element in formatted_recommendations:
        elements.append(element)
    
    elements.append(Spacer(1, 25))
    
    # Detailed Places Table (Enhanced)
    if search_results.get('places_data'):
        places_section = Paragraph("📊 Quick Reference Guide", subtitle_style)
        elements.append(places_section)
        elements.append(create_section_divider())
        elements.append(Spacer(1, 15))
        
        table = create_beautiful_places_table(search_results['places_data'])
        elements.append(table)
        elements.append(Spacer(1, 25))
    
    # Enhanced Chat History Section
    if conversation_history and len(conversation_history) > 2:
        elements.append(PageBreak())
        
        chat_header = Paragraph("💬 Your Travel Conversation", subtitle_style)
        elements.append(chat_header)
        elements.append(create_section_divider())
        elements.append(Spacer(1, 15))
        
        # Conversation summary
        follow_up_messages = conversation_history[2:] if len(conversation_history) > 2 else []
        summary_text = f"💡 This conversation contains {len(follow_up_messages)} personalized questions and detailed AI responses to help you plan your perfect trip."
        summary = Paragraph(summary_text, info_box_style)
        elements.append(summary)
        elements.append(Spacer(1, 20))
        
        # Format conversation beautifully
        chat_elements = format_conversation_history(follow_up_messages, chat_user_style, chat_ai_style, meta_style)
        for element in chat_elements:
            elements.append(element)
    
    elif conversation_history and len(conversation_history) <= 2:
        elements.append(Spacer(1, 20))
        no_chat_note = Paragraph(
            "💡 <i>Start a conversation with Travel Buddy! Ask follow-up questions about your destination, and they'll appear in your next PDF report with personalized answers.</i>", 
            ParagraphStyle('NoChat', parent=styles['Normal'], fontSize=11, 
                         alignment=TA_CENTER, textColor=colors.HexColor('#718096'),
                         backColor=colors.HexColor('#F7FAFC'), borderPadding=15,
                         borderColor=colors.HexColor('#E2E8F0'), borderWidth=1)
        )
        elements.append(no_chat_note)
    
    # Beautiful Footer
    elements.append(Spacer(1, 40))
    elements.append(create_section_divider())
    elements.append(Spacer(1, 15))
    
    footer_content = """
    <b>✈️ Travel Buddy App</b><br/>
    Your Personal AI Travel Companion<br/>
    <i>Crafted with ❤️ by Traveller Vishwa</i>
    """
    
    footer = Paragraph(footer_content, 
                      ParagraphStyle('BeautifulFooter', parent=styles['Normal'], 
                                   fontSize=10, alignment=TA_CENTER, 
                                   textColor=colors.HexColor('#718096'),
                                   leading=14))
    elements.append(footer)
    
    # Build PDF with error handling
    try:
        doc.build(elements)
    except Exception as e:
        logging.error(f"Error building PDF: {str(e)}")
        # Create fallback minimal PDF
        fallback_elements = [
            Paragraph("🌟 Travel Buddy Report", title_style),
            Spacer(1, 20),
            Paragraph(f"📍 Destination: {search_results.get('location', 'Unknown')}", place_detail_style),
            Spacer(1, 15),
            Paragraph("⚠️ An error occurred while generating the full report. Please try again.", place_detail_style),
            Spacer(1, 15),
            Paragraph("If the problem persists, please contact our support team.", place_detail_style)
        ]
        doc.build(fallback_elements)
    
    buffer.seek(0)
    return buffer

def format_ai_recommendations(ai_response, title_style, detail_style, info_style):
    """Parse and beautifully format AI recommendations"""
    elements = []
    
    if not ai_response:
        return elements
    
    # Clean the text first
    cleaned_text = clean_text_for_pdf(ai_response)
    
    # Split into sections - be more careful with regex
    sections = re.split(r'(?=###\s|####\s|\d+\.\s+<b>)', cleaned_text)
    
    for section in sections:
        if not section.strip():
            continue
            
        try:
            # Handle different section types
            if section.startswith('###'):
                # Main section header
                lines = section.split('<br/>')
                header_line = lines[0] if lines else section
                header_text = re.sub(r'#{2,4}\s*', '', header_line)
                
                if header_text.strip():
                    # Remove any remaining HTML tags from header
                    clean_header = re.sub(r'<[^>]+>', '', header_text.strip())
                    elements.append(Paragraph(f"🎯 {clean_header}", title_style))
                    elements.append(Spacer(1, 10))
                    
                    # Add remaining content if any
                    remaining_lines = lines[1:] if len(lines) > 1 else []
                    if remaining_lines:
                        remaining_content = '<br/>'.join(remaining_lines).strip()
                        if remaining_content:
                            elements.append(Paragraph(remaining_content, detail_style))
                            elements.append(Spacer(1, 15))
            
            elif re.match(r'\d+\.\s+<b>', section.strip()):
                # Numbered place entry
                place_elements = format_place_entry_safe(section, title_style, detail_style, info_style)
                elements.extend(place_elements)
            
            else:
                # Regular paragraph
                if section.strip():
                    elements.append(Paragraph(section.strip(), detail_style))
                    elements.append(Spacer(1, 10))
                    
        except Exception as e:
            # If formatting fails, add as plain text
            logging.warning(f"Failed to format section, using plain text: {str(e)}")
            plain_text = re.sub(r'<[^>]+>', '', section.strip())
            if plain_text:
                elements.append(Paragraph(plain_text, detail_style))
                elements.append(Spacer(1, 10))
    
    return elements

def format_place_entry_safe(entry_text, title_style, detail_style, info_style):
    """Safely format individual place entries with error handling"""
    elements = []
    
    try:
        lines = entry_text.strip().split('<br/>')
        if not lines:
            return elements
        
        # Extract place name and rating from first line
        first_line = lines[0].strip()
        place_match = re.match(r'(\d+)\.\s+<b>(.*?)</b>(?:\s*-\s*<b>Rating:</b>\s*([\d.]+))?', first_line)
        
        if place_match:
            number, place_name, rating = place_match.groups()
            
            # Create beautiful place header
            rating_stars = "⭐" * min(5, int(float(rating or 0))) if rating else ""
            place_header = f"{number}. {place_name} {rating_stars}"
            if rating:
                place_header += f" ({rating}/5)"
            
            elements.append(Paragraph(place_header, title_style))
            
            # Process remaining details safely
            details = []
            
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                
                # Extract different types of information
                if '<b>Address:</b>' in line:
                    address = re.sub(r'.*?<b>Address:</b>\s*', '', line)
                    address = re.sub(r'<[^>]+>', '', address)  # Remove any remaining tags
                    details.append(f"📍 <b>Location:</b> {address}")
                elif '<b>Description:</b>' in line:
                    desc = re.sub(r'.*?<b>Description:</b>\s*', '', line)
                    desc = re.sub(r'<[^>]+>', '', desc)  # Remove any remaining tags
                    details.append(f"📝 <b>About:</b> {desc}")
                elif '<b>Categories:</b>' in line:
                    categories = re.sub(r'.*?<b>Categories:</b>\s*', '', line)
                    categories = re.sub(r'<[^>]+>', '', categories)  # Remove any remaining tags
                    details.append(f"🏷️ <b>Type:</b> {categories}")
                else:
                    # Handle any other content
                    clean_line = re.sub(r'<[^>]+>', '', line)
                    if clean_line.strip():
                        details.append(clean_line.strip())
            
            # Add formatted details
            for detail in details:
                if detail.strip():
                    elements.append(Paragraph(detail.strip(), detail_style))
            
            elements.append(Spacer(1, 15))
            
    except Exception as e:
        # Fallback to plain text if anything goes wrong
        logging.warning(f"Failed to format place entry, using plain text: {str(e)}")
        plain_text = re.sub(r'<[^>]+>', '', entry_text.strip())
        if plain_text:
            elements.append(Paragraph(plain_text, detail_style))
            elements.append(Spacer(1, 15))
    
    return elements

def create_beautiful_places_table(places_data):
    """Create a beautifully formatted places table"""
    # Header with icons
    table_data = [['🏛️ Place Name', '⭐ Rating', '💰 Price', '📍 Location']]
    
    for place in places_data[:12]:  # Show top 12 places
        name = place.get('name', 'N/A')
        if len(name) > 35:
            name = name[:32] + "..."
        
        rating = place.get('rating', 'N/A')
        rating_display = f"{rating}/5" if rating != 'N/A' else 'N/A'
        
        price_level = place.get('price_level', 0)
        price_display = '💰' * price_level if price_level else 'N/A'
        
        address = place.get('vicinity', place.get('formatted_address', 'N/A'))
        if len(address) > 45:
            address = address[:42] + "..."
        
        table_data.append([name, rating_display, price_display, address])
    
    table = Table(table_data, colWidths=[2.5*inch, 1*inch, 0.8*inch, 2.2*inch])
    
    # Beautiful table styling
    table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2B6CB0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 15),
        ('TOPPADDING', (0, 0), (-1, 0), 15),
        
        # Data rows styling
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F8F9FA')]),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
    ]))
    
    return table

def format_conversation_history(messages, user_style, ai_style, meta_style):
    """Format conversation history with beautiful styling"""
    elements = []
    
    # Remove duplicates and get unique messages
    seen_messages = set()
    unique_messages = []
    
    for msg in messages:
        content = msg.get('content', '').strip()
        if content and len(content) > 10:  # Avoid very short messages
            msg_hash = hash(content.lower()[:100])
            if msg_hash not in seen_messages:
                seen_messages.add(msg_hash)
                unique_messages.append(msg)
    
    # Show last 20 messages for better context
    recent_messages = unique_messages[-20:] if len(unique_messages) > 20 else unique_messages
    
    for i, msg in enumerate(recent_messages, 1):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        
        if role == 'user':
            # Clean and limit user message length
            clean_content = clean_text_for_pdf(content)
            if len(clean_content) > 800:
                clean_content = clean_content[:800] + "..."
            
            user_text = f"<b>👤 You asked:</b><br/><br/>{clean_content}"
            try:
                elements.append(Paragraph(user_text, user_style))
            except Exception as e:
                # Fallback to plain text if formatting fails
                plain_text = f"You asked: {content[:500]}..."
                elements.append(Paragraph(plain_text, user_style))
            
        elif role == 'assistant':
            # Clean and limit AI response length  
            clean_content = clean_text_for_pdf(content)
            if len(clean_content) > 1200:
                clean_content = clean_content[:1200] + "..."
            
            ai_text = f"<b>🤖 Travel Buddy replied:</b><br/><br/>{clean_content}"
            try:
                elements.append(Paragraph(ai_text, ai_style))
            except Exception as e:
                # Fallback to plain text if formatting fails
                plain_text = f"Travel Buddy replied: {content[:500]}..."
                elements.append(Paragraph(plain_text, ai_style))
        
        # Add conversation flow indicator
        elements.append(Spacer(1, 8))
        
        # Add section break every 6 messages
        if i % 6 == 0 and i < len(recent_messages):
            elements.append(create_section_divider())
            elements.append(Spacer(1, 10))
    
    return elements

def clean_text_for_pdf(text):
    """Enhanced text cleaning for beautiful PDF formatting"""
    if not text:
        return ""
    
    # Replace problematic Unicode characters
    replacements = {
        '\u2019': "'", '\u2018': "'", 
        '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '--', 
        '\u2026': '...', '\u00a0': ' ',
        '\u2022': '•', '\u2023': '▶'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Clean up whitespace and formatting
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple newlines
    text = re.sub(r' +', ' ', text)  # Multiple spaces
    
    # First escape XML characters BEFORE processing markdown
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    
    # Now safely convert markdown to HTML
    # Handle bold markdown **text** -> <b>text</b>
    text = re.sub(r'\*\*([^*]+?)\*\*', r'<b>\1</b>', text)
    # Handle italic markdown *text* -> <i>text</i> (but avoid conflicting with **)
    text = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<i>\1</i>', text)
    
    # Handle line breaks
    text = text.replace('\n', '<br/>')
    
    # Remove any remaining problematic characters or sequences
    text = re.sub(r'<b>\s*</b>', '', text)  # Empty bold tags
    text = re.sub(r'<i>\s*</i>', '', text)  # Empty italic tags
    
    # Fix any nested or malformed tags
    text = re.sub(r'<b>([^<]*)<b>', r'<b>\1', text)  # Nested bold start
    text = re.sub(r'</b>([^>]*)</b>', r'\1</b>', text)  # Nested bold end
    text = re.sub(r'<i>([^<]*)<i>', r'<i>\1', text)  # Nested italic start
    text = re.sub(r'</i>([^>]*)</i>', r'\1</i>', text)  # Nested italic end
    
    return text.strip()