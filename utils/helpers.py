import streamlit as st
import pandas as pd
from datetime import datetime

def display_places_data(places_data, title):
    """Display places data in a formatted way"""
    if not places_data:
        st.warning(f"No {title.lower()} found for this location.")
        return
    
    st.subheader(f"📍 {title}")
    
    for i, place in enumerate(places_data[:5], 1):
        with st.expander(f"{i}. {place.get('name', 'Unknown Place')} ⭐ {place.get('rating', 'N/A')}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Address:** {place.get('vicinity', place.get('formatted_address', 'N/A'))}")
                if 'types' in place:
                    st.write(f"**Category:** {', '.join(place['types'][:2])}")
                if place.get('rating'):
                    st.write(f"**Rating:** {place['rating']} ⭐")
            
            with col2:
                if 'price_level' in place:
                    price_levels = {1: "$", 2: "$$", 3: "$$$", 4: "$$$$"}
                    st.write(f"**Price Level:** {price_levels.get(place['price_level'], 'N/A')}")
                
                if place.get('user_ratings_total'):
                    st.write(f"**Reviews:** {place['user_ratings_total']} reviews")

def create_summary_card(location, total_places, total_restaurants, total_activities, total_hotels):
    """Create a summary card with key statistics"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🏛️ Tourist Places", total_places)
    
    with col2:
        st.metric("🍽️ Restaurants", total_restaurants)
    
    with col3:
        st.metric("🎯 Activities", total_activities)
    
    with col4:
        st.metric("🏨 Hotels", total_hotels)

def format_ai_response(response):
    """Format AI response for better display"""
    # Split response into sections if it contains clear markers
    sections = response.split('\n\n')
    formatted_response = ""
    
    for section in sections:
        if section.strip():
            # Check if section starts with a number (numbered list)
            if section.strip()[0].isdigit():
                formatted_response += f"\n\n{section}"
            else:
                formatted_response += f"\n\n{section}"
    
    return formatted_response.strip()

def get_distance_options():
    """Get distance options for search radius"""
    return {
        "10 km": 10000,
        "25 km": 25000,
        "50 km": 50000,
        "100 km": 100000
    }