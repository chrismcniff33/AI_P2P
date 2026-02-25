import streamlit as st
import hmac
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import re
import random
from collections import Counter

# --- 1. PAGE CONFIGURATION & STYLING ---
st.set_page_config(page_title="AI Path to Purchase", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
        .block-container {padding-top: 5rem; padding-bottom: 2rem;}
        h1 {color: #1e293b; font-family: 'Helvetica Neue', sans-serif; margin-bottom: 0.5rem;}
        
        /* Custom Metric Card Styling */
        .custom-metric {
            background-color: #f8fafc;
            padding: 20px;
            border-radius: 8px;
            border-left: 5px solid #6366f1;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            height: 100%;
        }
        
        /* Native Tab Styling Improvements */
        .stTabs [data-baseweb="tab-list"] {gap: 8px; border-bottom: 2px solid #e5e7eb; margin-top: 0.5rem;}
        .stTabs [data-baseweb="tab"] {
            height: 45px; 
            white-space: pre-wrap; 
            background-color: #f1f5f9; 
            border-radius: 5px 5px 0px 0px; 
            padding: 10px 20px;
            font-weight: 600;
        }
        .stTabs [aria-selected="true"] {
            background-color: #4f46e5 !important; 
            color: white !important;
        }
        
        /* Custom LLM Reasoning Box */
        .llm-box {
            background-color: #f0fdf4;
            border: 1px solid #bbf7d0;
            padding: 15px;
            border-radius: 8px;
            color: #166534;
            font-size: 14px;
            margin-top: 10px;
        }
        .llm-box-negative {
            background-color: #fef2f2;
            border: 1px solid #fecaca;
            padding: 15px;
            border-radius: 8px;
            color: #991b1b;
            font-size: 14px;
            margin-top: 10px;
        }
        .llm-box-neutral {
            background-color: #fffbeb;
            border: 1px solid #fde68a;
            padding: 15px;
            border-radius: 8px;
            color: #92400e;
            font-size: 14px;
            margin-top: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. PASSWORD PROTECTION ---
def check_password():
    def password_entered():
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Please enter the company password to access this tool:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Please enter the company password to access this tool:", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if not check_password():
    st.stop()

# --- 3. DATA LOADING & ENGINEERING ---
@st.cache_data
def load_and_enrich_data():
    try:
        df = pd.read_csv("ultimate_ai_dataset_contextual.zip")
        df['date'] = pd.to_datetime(df['date'], dayfirst=True, format='mixed')
    except:
        st.error("❌ Data not found. Please upload 'ultimate_ai_dataset_contextual.zip' to your repo.")
        st.stop()

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
    
    if 'criteria' not in df.columns:
        criteria_map = {
            "Shampoo": ["Scalp care", "Budget", "Damaged hair", "Color protection", "Premium", "Volume"],
            "TVs": ["Gaming", "Budget", "OLED", "Large screen", "Smart TV", "Sound quality"],
            "Dog food": ["Puppy", "Grain-free", "Senior", "Weight management", "Sensitive stomach", "High protein"],
            "Dietary supplements": ["Immunity", "Sleep", "Energy", "Joint support", "Gut health", "Focus"]
        }
        df['criteria'] = df['category'].apply(lambda x: random.choice(criteria_map.get(x, ["General"])))
    
    known_brands = [
        "Suave", "Garnier", "Pantene", "Herbal Essences", "Aussie", "Tresemmé", "Dove", "L'Oréal", "Head & Shoulders", "Old Spice",
        "Aveeno", "OGX", "Maui Moisture", "SheaMoisture", "Kristen Ess", "Nexxus", "Paul Mitchell", "Biolage", "Monday", "Native",
        "Olaplex", "Pureology", "Briogeo", "Kérastase", "Moroccanoil", "Redken", "Living Proof", "Oribe", "Kevin Murphy", "Drunk Elephant",
        "Seda", "Skala", "Monange", "Palmolive", "Niely Gold", "Darling", "Yamasterol", "Kanechom", "Origem", "Salon Line",
        "Natura", "O Boticário", "Haskell", "Bio Extratus", "Amend", "Inoar", "Yenzah", "Truss", "Braé", "L'Occitane", "Lowell", "Keune", "Senscience", "Joico",
        "Clinic Plus", "Sunsilk", "Chik", "Vatika", "Himalaya", "Meera", "Ayur", "Indulekha", "Biotique", "Khadi", "Forest Essentials", "Kama Ayurveda", "Wella",
        "Mamaearth", "Wow Skin Science", "Plum", "Arata", "mCaffeine", "Juicy Chemistry", "Bare Anatomy", "True Frog", "WishCare",
        "Samsung", "LG", "Sony", "TCL", "Hisense", "Vizio", "Philips", "Panasonic", "Sharp", "Toshiba", "Roku", "Insignia", "Element", "Westinghouse", "Sceptre",
        "Xiaomi", "OnePlus", "Realme", "Vu", "Thomson", "Kodak", "iFFALCON", "Acer", "Blaupunkt", "Infinix", "Motorola", "Sansui", "Haier", "Compaq", "Nokia",
        "Coocaa", "Polytron", "Changhong", "Akari", "Konka", "Skyworth", "Huawei", "Honor", "Oppo", "Vidda",
        "Pedigree", "Purina", "Kibbles 'n Bits", "Gravy Train", "Ol' Roy", "Alpo", "Beneful", "Cesar", "Iams", "Rachael Ray", "Diamond Naturals", "Taste of the Wild", "Blue Buffalo", "Nutro", "Wellness", "Canidae", "Merrick",
        "Royal Canin", "Hill's", "Orijen", "Acana", "Ziwi Peak", "Primal", "Stella & Chewy's", "Instinct", "Fromm", "Open Farm", "The Farmer's Dog", "Ollie", "Spot & Tango", "Jinx", "Sundays", "Nom Nom", "Wild Earth",
        "Drools", "Meat Up", "Chappi", "Purepet", "SmartHeart", "Fidele", "Canine Creek", "Farmina", "Arden Grange", "Goodness", "Kennel Kitchen", "Chip Chops", "Heads Up For Tails", "Blep", "Doggie Dabbas", "Goofy Tails", "Captain Zack", "Wiggles",
        "Nature Made", "Centrum", "Kirkland", "Equate", "Spring Valley", "Emergen-C", "One A Day", "Sundown", "Nature's Bounty", "Vitafusion",
        "NOW Foods", "SmartyPants", "GNC", "Nordic Naturals", "Solgar", "Jarrow", "Doctor's Best", "MegaFood", "New Chapter", "Rainbow Light",
        "Thorne", "Garden of Life", "Pure Encapsulations", "Douglas Laboratories", "Metagenics", "Standard Process", "Klaire Labs", "Designs for Health", "Xymogen", "Life Extension",
        "Ritual", "Care/of", "Athletic Greens", "AG1", "Hum Nutrition", "Vital Proteins", "Seed", "Moon Juice", "Sakara", "Persona", "Bulletproof",
        "HealthKart", "Patanjali", "Dabur", "Baidyanath", "Organic India", "Zandu", "Nutrilite", "Becosules", "Shelcal", "TrueBasics", "MuscleBlaze", "Revital", "Seven Seas", "Fast&Up", "Optimum Nutrition", "BigMuscles", "MyProtein", "Wellbeing Nutrition", "Oziva", "Kapiva", "Power Gummies", "Plix", "Setu", "Man Matters", "Boldfit"
    ]
    
    brand_patterns = {brand: re.compile(re.escape(brand), re.IGNORECASE) for brand in known_brands}

    def extract_brands_nlp(text):
        found = []
        text_str = str(text)
        for brand, pattern in brand_patterns.items():
            if pattern.search(text_str):
                found.append(brand)
        return found
    
    df['mentioned_brands'] = df['response'].apply(extract_brands_nlp)
    df_exploded = df.explode('mentioned_brands').dropna(subset=['mentioned_brands'])
    
    return df, df_exploded

df, df_exploded = load_and_enrich_data()

if df_exploded.empty:
    st.error("⚠️ No brands were detected! Check dataset generation.")
    st.stop()


# --- 4. TOP LEVEL NAVIGATION ---
st.title("AI Path to Purchase")

# Native Clickable Tabs Ribbon
tab_insight, tab_sov, tab_semantic, tab_sources = st.tabs([
    "👁️ Share of Voice Overview", 
    "📊 Competitor Benchmarking", 
    "🔍 Search Criteria & Perception", 
    "🔗 Source Intelligence"
])


# === TAB 1: SHARE OF VOICE OVERVIEW ===
with tab_insight:
    # --- Tab-Specific Filters ---
    st.markdown("<div style='padding-top: 10px;'></div>", unsafe_allow_html=True)
    c1_1, c2_1 = st.columns(2)
    cat_1 = c1_1.selectbox("📂 Select Category", sorted(df['category'].unique()), key='cat_1', help="Filter Tab 1 metrics by specific product category")
    scope_df_1 = df_exploded[df_exploded['category'] == cat_1]
    
    if not scope_df_1.empty:
        brands_1 = scope_df_1['mentioned_brands'].value_counts().head(50).index.tolist()
        brand_1 = c2_1.selectbox("🎯 Select Focus Brand", brands_1, index=0, key='brand_1', help="Select the core brand to benchmark against the industry")
    else:
        st.warning("No data for this category.")
        st.stop()
        
    st.markdown("---")
    
    st.subheader("Global AI Visibility Metrics", help="High-level summary of your brand's footprint across all monitored Generative AI platforms.")
    
    # EXACT WEEKLY INDUSTRY AVERAGE LOGIC
    wk_totals = scope_df_1.groupby('date').size().reset_index(name='total')
    wk_brands = scope_df_1.groupby(['date', 'mentioned_brands']).size().reset_
