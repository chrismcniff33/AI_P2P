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
        df['date'] = pd.to_datetime(df['date'], dayfirst=True, format='mixed')
    except:
        st.error("❌ Data not found. Please upload 'ultimate_ai_dataset_contextual.zip' to your repo.")
        st.stop()

    # --- A. INJECT DUMMY SOURCES ---
    # FIXED: Added missing quotes and ensured proper dictionary structure
    source_db = {
        "Shampoo": ["Allure Magazine", "Reddit r/HaircareScience", "Sephora Reviews", "Vogue Beauty", "Byrdie", "YouTube (Brad Mondo)", "MakeupAlley"],
        "TVs": ["RTings.com", "The Verge", "Reddit r/4kTV", "CNET", "TechRadar", "YouTube (Linus Tech Tips)", "Consumer Reports"],
        "Dog food": ["DogFoodAdvisor", "Reddit r/dogs", "Chewy.com Reviews", "AKC.org", "Veterinary Partner", "PetMD"],
        "Dietary supplements": ["Examine.com", "Healthline", "NIH.gov", "Amazon Reviews", "Labdoor", "Reddit r/Supplements"]
    }

    def assign_source(row):
        cat_sources = source_db.get(row['category'], ["General Web Search"])
        return random.choice(cat_sources)

    df['source_citation'] = df.apply(assign_source, axis=1)
    
    # --- B. EXTRACT BRANDS ---
    def extract_brands_list(text):
        # Extract text between double asterisks (e.g. **Samsung**)
        return re.findall(r'\*\*(.*?)\*\*', str(text))
    
    df['mentioned_brands'] = df['response'].apply(extract_brands_list)
    
    # Explode dataset (One row per brand mention)
    df_exploded = df.explode('mentioned_brands')
    
    # Clean up (Remove empty/NaN brands)
    df_exploded = df_exploded.dropna(subset=['mentioned_brands'])
    
    return df, df_exploded

df, df_exploded = load_and_enrich_data()

# --- DATA CHECK ---
if df_exploded.empty:
    st.error("⚠️ No brands were found in the data! The dashboard looks for brands bolded like **BrandName**.")
    st.stop()

# --- 4. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🚀 BrandAI")
    
    st.subheader("1. Define Market Scope")
    # Sort categories alphabetically
    selected_category = st.selectbox("Category", sorted(df['category'].unique()))
    
    # Filter countries based on category
    avail_countries = sorted(df[df['category'] == selected_category]['country'].unique())
    selected_country = st.selectbox("Market (Country)", ["All"] + avail_countries)
    
    # Filter Data
    scope_df = df_exploded[df_exploded['category'] == selected_category]
    if selected_country != "All":
        scope_df = scope_df[scope_df['country'] == selected_country]
        
    st.subheader("2. Select Your Brand")
    if not scope_df.empty:
        # Get top 50 brands for the dropdown to avoid clutter
        available_brands = scope_df['mentioned_brands'].value_counts().head(50).index.tolist()
        target_brand = st.selectbox("Focus Brand", available_brands)
    else:
        st.warning("No data for this selection.")
        st.stop()
    
    st.markdown("---")
    st.info(f"Analyzing {len(scope_df):,} mentions.")

# --- 5. MAIN DASHBOARD ---
st.title(f"Brand Intelligence: {target_brand}")

# TOP NAVIGATION BAR (Tabs)
tab_insight, tab_sov, tab_semantic, tab_sources = st.tabs([
    "💡 Executive Insights", 
    "📊 Share of Voice", 
    "💬 Brand Perception", 
    "🔗 Source Intelligence"
])

# === TAB 1: EXECUTIVE INSIGHTS (SWOT) ===
with tab_insight:
    st.header(f"Executive Summary")
    
    # A. KPI CARDS
    total_mentions = len(scope_df)
    brand_mentions = len(scope_df[scope_df['mentioned_brands'] == target_brand])
    sov = (brand_mentions / total_mentions) * 100 if total_mentions > 0 else 0
    
    rank_df = scope_df['mentioned_brands'].value_counts().reset_index()
    rank_df.columns = ['Brand', 'Count']
    try:
        rank = rank_df[rank_df['Brand'] == target_brand].index[0] + 1
    except:
        rank = "N/A"

    try:
        top_competitor = rank_df[rank_df['Brand'] != target_brand].iloc[0]['Brand']
    except:
        top_competitor = "None"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Share of Voice", f"{sov:.1f}%")
    c2.metric("Market Rank", f"#{rank}")
    c3.metric("Total Mentions", f"{brand_mentions:,}")
    c4.metric("Top Competitor", top_competitor)

    st.markdown("---")
    
    # B. STRENGTHS & WEAKNESSES
    col_vis, col_text = st.columns([1, 1])
    
    # Calculate Brand SoV per Criteria
    crit_counts = scope_df
