import streamlit as st
from modules.engine import GameDirector

# Global initialization
if "director" not in st.session_state:
    st.session_state.director = GameDirector()
