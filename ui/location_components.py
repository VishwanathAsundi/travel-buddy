import streamlit as st
from streamlit_js_eval import get_geolocation
import datetime

def render_current_location_component():
    # Trigger the get geolocation JS only on button click
    lat = st.session_state.get('lat', None)
    lng = st.session_state.get('lng', None)

    if not lat or not lng:
        if st.button("📡 Use My Location"):
            location = get_geolocation()
            if location:
                # st.session_state['lat'] = location.get('lat')
                # st.session_state['lng'] = location.get('lng')
                st.success("📍 Location retrieved!")
    else:
        st.info(f"📍 Your Location: Latitude: **{lat}**, Longitude: **{lng}**")

