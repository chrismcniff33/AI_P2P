import streamlit as st
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
        /* FIX: Increased padding-top to 5rem to prevent clipping by the Streamlit header */
        .block-container {padding-top: 5rem; padding-bottom: 2rem;}
        
        h1 {color: #1e293b; font-family: 'Helvetica Neue', sans-serif; margin-bottom: 1.5rem;}
        .metric-card {background-color: #f8fafc; padding: 20px; border-radius: 8px; border-left: 5px solid #6366f1;}
        div[data-testid="stMetricValue"] {font-size: 1.3rem; color: #4F46E5;}
        div[data-testid="stMetricDelta"] {font-size: 1rem;}
        
        /* Tab Styling */
        .stTabs [data-baseweb="tab-list"] {gap: 10px; border-bottom: 1px solid #e5e7eb; margin-top: 1rem;}
        .stTabs [data-baseweb="tab"] {
            height: 50px; 
            white-space: pre-wrap; 
            background-color: #f1f5f9; 
            border-radius: 5px 5px 0px 0px; 
            padding: 10px 20px;
        }
        .stTabs [aria-selected="true"] {background-color: #4f46e5; color: white;}
        
        /* Centering for the login section */
        .login-box {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. PASSWORD PROTECTION ---
def check_password():
    """Returns True if the user had the correct password."""
    def password_entered():
        if st.session_state["password"] == st.secrets["passwords"]["dashboard_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    # FIX: Using columns and line breaks to ensure correct alignment and visibility
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔐 Dashboard Access")
        st.text_input(
            "Please enter the password to access the dashboard", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        if st.session_state.get("password_correct") == False:
            st.error("😕 Password incorrect")
    return False

if not check_password():
    st.stop()

# --- 3. DATA LOADING & ENGINEERING ---
@st.cache_data
def load_and_enrich_data():
    try:
        # Assumes the zip file is in the root directory
        df = pd.read_csv("ultimate_ai_dataset_contextual.zip")
        df['date'] = pd.to_datetime(df['date'], dayfirst=True, format='mixed')
    except Exception as e:
        st.error(f"❌ Data not found: {e}. Please upload 'ultimate_ai_dataset_contextual.zip' to your repo.")
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


# --- 4. TOP LEVEL NAVIGATION & FILTERS ---
st.title("🚀 AI Path to Purchase")

# Global Filters
col_cat, col_brand = st.columns(2)

with col_cat:
    selected_category = st.selectbox("📂 Select Category", sorted(df['category'].unique()))
    scope_df = df_exploded[df_exploded['category'] == selected_category]

with col_brand:
    if not scope_df.empty:
        available_brands = scope_df['mentioned_brands'].value_counts().head(50).index.tolist()
        target_brand = st.selectbox("🎯 Select Focus Brand", available_brands, index=0)
    else:
        st.warning("No data for this category.")
        st.stop()

# --- 5. MAIN TABS ---
tab_insight, tab_sov, tab_semantic, tab_sources = st.tabs([
    "👁️ Share of Voice Overview", 
    "📊 Share of Voice Trends", 
    "💬 Brand Perception", 
    "🔗 Source Intelligence"
])

# === TAB 1: SHARE OF VOICE OVERVIEW ===
with tab_insight:
    st.markdown("### Global AI Visibility Metrics")
    
    global_mentions = len(scope_df)
    brand_mentions = len(scope_df[scope_df['mentioned_brands'] == target_brand])
    global_sov = (brand_mentions / global_mentions) * 100 if global_mentions > 0 else 0
    
    num_brands = len(scope_df['mentioned_brands'].unique())
    ind_avg_sov = 100.0 / num_brands if num_brands > 0 else 0
    
    ratio = global_sov / ind_avg_sov if ind_avg_sov > 0 else 0
    if ratio < 0.5: visibility = "Low 🔴"
    elif ratio < 1.2: visibility = "Average 🟡"
    else: visibility = "Excellent 🌟"
    
    leader = scope_df['mentioned_brands'].value_counts().index[0]
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Visibility vs Industry", visibility, f"SoV: {global_sov:.1f}%")
    col2.metric("Category Leader", leader)
    col3.metric("Total Mentions", f"{brand_mentions:,}")
    col4.metric("Industry Average", f"{ind_avg_sov:.1f}%")

    st.markdown("---")
    
    # Strategic Heatmap
    st.markdown("### Strategic Heatmap: Geographies vs AI Platforms")
    hm_totals = scope_df.groupby(['country', 'AI platform']).size().reset_index(name='total')
    hm_brand = scope_df[scope_df['mentioned_brands'] == target_brand].groupby(['country', 'AI platform']).size().reset_index(name='brand_count')
    hm_df = pd.merge(hm_totals, hm_brand, on=['country', 'AI platform'], how='left').fillna(0)
    hm_df['sov'] = (hm_df['brand_count'] / hm_df['total']) * 100
    
    hm_pivot = hm_df.pivot(index='country', columns='AI platform', values='sov')
    fig_hm = px.imshow(hm_pivot, aspect="auto", color_continuous_scale="YlGnBu", labels=dict(color="SoV %"))
    st.plotly_chart(fig_hm, use_container_width=True)

# === TAB 2: SHARE OF VOICE TRENDS ===
with tab_sov:
    st.header("Competitive Share of Voice Analysis")
    daily_counts = scope_df.groupby(['date', 'mentioned_brands']).size().reset_index(name='count')
    daily_totals = daily_counts.groupby('date')['count'].transform('sum')
    daily_counts['sov_pct'] = (daily_counts['count'] / daily_totals) * 100
    
    top_10 = scope_df['mentioned_brands'].value_counts().head(10).index.tolist()
    if target_brand not in top_10: top_10.append(target_brand)
    
    filtered_daily = daily_counts[daily_counts['mentioned_brands'].isin(top_10)]
    fig_time = px.line(filtered_daily, x='date', y='sov_pct', color='mentioned_brands', markers=True)
    st.plotly_chart(fig_time, use_container_width=True)

# === TAB 3: BRAND PERCEPTION (NLP) ===
with tab_semantic:
    st.header(f"How LLMs Describe '{target_brand}'")
    brand_responses = df[df['response'].str.contains(target_brand, case=False, na=False)]['response']
    
    all_words = []
    stopwords = {'the', 'and', 'is', 'for', 'with', 'this', 'that', 'are'}
    for resp in brand_responses:
        words = re.sub(r'[^\w\s]', '', resp.lower()).split()
        all_words.extend([w for w in words if w not in stopwords and w != target_brand.lower()])
    
    if all_words:
        word_counts = Counter(all_words).most_common(15)
        wc_df = pd.DataFrame(word_counts, columns=['Keyword', 'Frequency'])
        fig_bar = px.bar(wc_df, x='Frequency', y='Keyword', orientation='h', color='Frequency')
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Insufficient text data for descriptors.")

# === TAB 4: SOURCE INTELLIGENCE ===
with tab_sources:
    st.header("Source Citation Analysis")
    brand_source_df = scope_df[scope_df['mentioned_brands'] == target_brand]
    if not brand_source_df.empty:
        source_counts = brand_source_df['source_citation'].value_counts().reset_index()
        source_counts.columns = ['Source', 'Mentions']
        fig_tree = px.treemap(source_counts, path=['Source'], values='Mentions', color='Mentions')
        st.plotly_chart(fig_tree, use_container_width=True)
    else:
        st.warning("No source data for this brand.")
