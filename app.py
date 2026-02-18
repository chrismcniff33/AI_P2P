import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import random
from collections import Counter

# --- 1. PAGE CONFIGURATION & STYLING ---
st.set_page_config(page_title="BrandAI: Strategic Intelligence", page_icon="🚀", layout="wide")

# Custom CSS for a professional "Top Bar" feel
st.markdown("""
    <style>
        .block-container {padding-top: 1rem; padding-bottom: 2rem;}
        h1 {color: #1e293b; font-family: 'Helvetica Neue', sans-serif;}
        .metric-card {background-color: #f8fafc; padding: 20px; border-radius: 8px; border-left: 5px solid #6366f1;}
        div[data-testid="stMetricValue"] {font-size: 1.5rem; color: #4F46E5;}
        /* Make tabs more visible */
        .stTabs [data-baseweb="tab-list"] {gap: 10px; border-bottom: 1px solid #e5e7eb;}
        .stTabs [data-baseweb="tab"] {height: 50px; white-space: pre-wrap; background-color: #f1f5f9; border-radius: 5px 5px 0px 0px; padding: 10px 20px;}
        .stTabs [aria-selected="true"] {background-color: #4f46e5; color: white;}
    </style>
""", unsafe_allow_html=True)

# --- 2. PASSWORD PROTECTION ---
def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        if st.session_state["password"] == st.secrets["passwords"]["dashboard_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.text_input("Please enter the password to access the dashboard", type="password", on_change=password_entered, key="password")
    return False

if not check_password():
    st.stop()

# --- 3. DATA LOADING & ENGINEERING ---
@st.cache_data
def load_and_enrich_data():
    try:
        # Load ZIP (Pandas handles compression automatically)
        df = pd.read_csv("ultimate_ai_dataset_contextual.zip")
        # Flexible date parsing to handle multiple formats
        df['date'] = pd.to_datetime(df['date'], dayfirst=True, format='mixed')
    except:
        st.error("❌ Data not found. Please upload 'ultimate_ai_dataset_contextual.zip' to your repo.")
        st.stop()

    # --- A. INJECT DUMMY SOURCES ---
    source_db = {
        "Shampoo": ["Allure Magazine", "Reddit r/HaircareScience
