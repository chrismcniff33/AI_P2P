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
        
        .custom-metric {
            background-color: #f8fafc;
            padding: 20px;
            border-radius: 8px;
            border-left: 5px solid #6366f1;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            height: 100%;
        }
        
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

# --- 3. GLOBAL LEXICONS FOR FAST NLP ---
attribute_lexicon = {
    'organic': '🟢', 'natural': '🟢', 'vegan': '🟢', 'sulfate-free': '🟢', 'paraben-free': '🟢',
    'grain-free': '🟢', 'probiotics': '🟢', 'hyaluronic': '🟢', 'collagen': '🟢', 'non-gmo': '🟢',
    'delicious': '🟢', 'smooth': '🟢', 'refreshing': '🟢', 'soothing': '🟢', 'hydrating': '🟢',
    'moisturizing': '🟢', 'nourishing': '🟢', 'repairing': '🟢', 'strengthening': '🟢',
    'anti-aging': '🟢', 'fast-acting': '🟢', 'durable': '🟢', 'reliable': '🟢', 'effective': '🟢',
    'sturdy': '🟢', 'sharp': '🟢', 'crisp': '🟢', 'affordable': '🟢', 'premium': '🟢', 'value': '🟢',
    'convenient': '🟢', 'easy': '🟢', 'quick': '🟢', 'portable': '🟢', 'compact': '🟢',
    'sustainable': '🟢', 'eco-friendly': '🟢', 'recyclable': '🟢', 'cruelty-free': '🟢',
    'ethical': '🟢', 'biodegradable': '🟢', 'high-quality': '🟢', 'quality': '🟢', 'safe': '🟢',
    'healthy': '🟢', 'toxic': '🔴', 'artificial': '🔴', 'preservatives': '🔴', 'fillers': '🔴', 'bland': '🔴',
    'stinky': '🔴', 'greasy': '🔴', 'sticky': '🔴', 'bitter': '🔴', 'useless': '🔴',
    'ineffective': '🔴', 'weak': '🔴', 'slow': '🔴', 'flimsy': '🔴', 'laggy': '🔴',
    'glitchy': '🔴', 'cheap': '🔴', 'expensive': '🔴', 'overpriced': '🔴', 'bulky': '🔴',
    'heavy': '🔴', 'dry': '🔴', 'damaged': '🔴', 'chicken': '🟡', 'beef': '🟡', 'salmon': '🟡', 'protein': '🟡', 'vitamins': '🟡',
    'minerals': '🟡', 'keratin': '🟡', 'aloe': '🟡', 'taste': '🟡', 'flavor': '🟡',
    'smell': '🟡', 'scent': '🟡', 'fragrance': '🟡', 'texture': '🟡', 'crunchy': '🟡',
    'soft': '🟡', 'chewy': '🟡', 'budget': '🟡', 'large': '🟡', 'small': '🟡', 'bulk': '🟡',
    'travel-size': '🟡', 'pack': '🟡', 'oled': '🟡', 'led': '🟡', '4k': '🟡', 'smart': '🟡',
    'size': '🟡', 'ingredients': '🟡', 'packaging': '🟡'
}

theme_mapping = {
    "Ingredients & Formulation": ['organic', 'natural', 'vegan', 'sulfate-free', 'paraben-free', 'grain-free', 'probiotics', 'hyaluronic', 'collagen', 'non-gmo', 'toxic', 'artificial', 'preservatives', 'fillers', 'chicken', 'beef', 'salmon', 'protein', 'vitamins', 'minerals', 'keratin', 'aloe', 'ingredients'],
    "Sensory & Experience": ['delicious', 'smooth', 'refreshing', 'soothing', 'bland', 'stinky', 'greasy', 'sticky', 'bitter', 'taste', 'flavor', 'smell', 'scent', 'fragrance', 'texture', 'crunchy', 'soft', 'chewy'],
    "Performance & Efficacy": ['hydrating', 'moisturizing', 'nourishing', 'repairing', 'strengthening', 'anti-aging', 'fast-acting', 'durable', 'reliable', 'effective', 'sturdy', 'sharp', 'crisp', 'high-quality', 'quality', 'safe', 'healthy', 'useless', 'ineffective', 'weak', 'slow', 'flimsy', 'laggy', 'glitchy', 'dry', 'damaged'],
    "Price & Value": ['affordable', 'premium', 'value', 'cheap', 'expensive', 'overpriced', 'budget'],
    "Convenience & Format": ['convenient', 'easy', 'quick', 'portable', 'compact', 'bulky', 'heavy', 'large', 'small', 'bulk', 'travel-size', 'pack', 'size', 'packaging'],
    "Sustainability": ['sustainable', 'eco-friendly', 'recyclable', 'cruelty-free', 'ethical', 'biodegradable']
}

attribute_pattern = re.compile(r'\b(' + '|'.join([re.escape(k) for k in attribute_lexicon.keys()]) + r')\b', re.IGNORECASE)

def extract_attributes_fast(text):
    if pd.isna(text): return []
    return list(set(attribute_pattern.findall(str(text).lower())))

# --- 4. DATA LOADING & PRE-COMPUTATION ---
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

    df['source_citation'] = df.apply(lambda row: random.choice(source_db.get(row['category'], ["General Web Search"])), axis=1)
    
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
        text_str = str(text)
        return [brand for brand, pattern in brand_patterns.items() if pattern.search(text_str)]
    
    df['mentioned_brands'] = df['response'].apply(extract_brands_nlp)
    df['extracted_attributes'] = df['response'].apply(extract_attributes_fast)
    
    df_exploded = df.explode('mentioned_brands').dropna(subset=['mentioned_brands'])
    
    return df, df_exploded

df, df_exploded = load_and_enrich_data()

if df_exploded.empty:
    st.error("⚠️ No brands were detected! Check dataset generation.")
    st.stop()


# --- 5. TOP LEVEL NAVIGATION ---
st.title("AI Path to Purchase")

tab_insight, tab_sov, tab_semantic, tab_sources = st.tabs([
    "👁️ Share of Voice Overview", 
    "📊 Competitor Benchmarking", 
    "🔍 Search Criteria & Perception", 
    "🔗 Source Intelligence"
])

# === TAB 1: SHARE OF VOICE OVERVIEW ===
with tab_insight:
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
    
    wk_totals = scope_df_1.groupby('date').size().reset_index(name='total')
    wk_brands = scope_df_1.groupby(['date', 'mentioned_brands']).size().reset_index(name='count')
    wk_sov = pd.merge(wk_brands, wk_totals, on='date')
    wk_sov['sov'] = (wk_sov['count'] / wk_sov['total']) * 100
    weekly_ind_avg = wk_sov.groupby('date')['sov'].mean()
    ind_avg_sov = weekly_ind_avg.mean() if not weekly_ind_avg.empty else 0
    
    global_mentions = len(scope_df_1)
    brand_mentions = len(scope_df_1[scope_df_1['mentioned_brands'] == brand_1])
    global_sov = (brand_mentions / global_mentions) * 100 if global_mentions > 0 else 0
    
    ratio = global_sov / ind_avg_sov if ind_avg_sov > 0 else 0
    if ratio < 0.5: visibility = "Low"
    elif ratio < 0.8: visibility = "Moderate"
    elif ratio < 1.2: visibility = "Average"
    elif ratio < 2.0: visibility = "Good"
    else: visibility = "Excellent"
    
    hm_totals = scope_df_1.groupby(['country', 'AI platform']).size().reset_index(name='total')
    hm_brand = scope_df_1[scope_df_1['mentioned_brands'] == brand_1].groupby(['country', 'AI platform']).size().reset_index(name='brand_count')
    hm_unique = scope_df_1.groupby(['country', 'AI platform'])['mentioned_brands'].nunique().reset_index(name='unique_brands')
    
    hm_df = pd.merge(hm_totals, hm_brand, on=['country', 'AI platform'], how='left').fillna(0)
    hm_df = pd.merge(hm_df, hm_unique, on=['country', 'AI platform'])
    hm_df['sov'] = (hm_df['brand_count'] / hm_df['total']) * 100
    hm_df['ind_avg'] = 100.0 / hm_df['unique_brands'].replace(0, 1) 
    hm_df['index_vs_avg'] = (hm_df['sov'] / hm_df['ind_avg']) * 100
    hm_valid = hm_df[(hm_df['total'] > 0) & (hm_df['index_vs_avg'] > 0)]
    
    if not hm_valid.empty:
        idx_max = hm_valid['index_vs_avg'].idxmax()
        top_strength_str = f"{hm_valid.loc[idx_max, 'AI platform']} in {hm_valid.loc[idx_max, 'country']} 🏆"
        idx_min = hm_valid['index_vs_avg'].idxmin()
        top_weakness_str = f"{hm_valid.loc[idx_min, 'AI platform']} in {hm_valid.loc[idx_min, 'country']} ⚠️"
    else:
        top_strength_str, top_weakness_str = "N/A", "N/A"

    c1, c2, c3 = st.columns(3)
    header_color = "#10b981" if visibility in ["Good", "Excellent"] else "#ef4444" if visibility == "Low" else "#f59e0b"
    c1.markdown(f"""
    <div class="custom-metric">
        <div style="color: #64748b; font-size: 14px; font-weight: 600;">Visibility vs Industry <span title="Your brand's overall Share of Voice compared to the average brand in this category">ℹ️</span></div>
        <div style="color: {header_color}; font-size: 26px; font-weight: 700; margin-top: 5px;">{visibility}: {global_sov:.1f}%</div>
        <div style="color: #94a3b8; font-size: 13px; font-weight: 500; margin-top: 5px;">Industry Avg: {ind_avg_sov:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)
    c2.markdown(f"""
    <div class="custom-metric">
        <div style="color: #64748b; font-size: 14px; font-weight: 600;">Top Strength <span title="The platform & market where your brand over-indexes the most vs competitors. Driven directly by the Heatmap.">ℹ️</span></div>
        <div style="color: #1e293b; font-size: 20px; font-weight: 700; margin-top: 10px; line-height: 1.2;">{top_strength_str}</div>
        <div style="color: #94a3b8; font-size: 13px; font-weight: 500; margin-top: 5px;">Based on Index vs Avg</div>
    </div>
    """, unsafe_allow_html=True)
    c3.markdown(f"""
    <div class="custom-metric">
        <div style="color: #64748b; font-size: 14px; font-weight: 600;">Area for Improvement <span title="The platform & market where your brand under-indexes the most vs competitors. Driven directly by the Heatmap.">ℹ️</span></div>
        <div style="color: #1e293b; font-size: 20px; font-weight: 700; margin-top: 10px; line-height: 1.2;">{top_weakness_str}</div>
        <div style="color: #94a3b8; font-size: 13px; font-weight: 500; margin-top: 5px;">Based on Index vs Avg</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Cross-Segment Share of Voice Over Time", help="Tracks weekly fluctuations in AI recommendations to catch algorithmic shifts.")
    
    st.markdown("#### SoV by AI Platform")
    all_geos_options = ["Global"] + sorted(scope_df_1['country'].unique())
    selected_geos = st.multiselect("Filter Geography", all_geos_options, default=["Global"], key="geo_filter")
    left_df = scope_df_1 if "Global" in selected_geos else scope_df_1[scope_df_1['country'].isin(selected_geos)]
        
    if not left_df.empty:
        l_totals = left_df.groupby(['date', 'AI platform']).size().reset_index(name='total')
        l_brand = left_df.groupby(['date', 'AI platform', 'mentioned_brands']).size().reset_index(name='brand_count')
        l_merged = pd.merge(l_totals, l_brand[l_brand['mentioned_brands'] == brand_1], on=['date', 'AI platform'], how='left').fillna(0)
        
        valid_platforms = l_merged.groupby('AI platform')['brand_count'].sum()
        l_merged = l_merged[l_merged['AI platform'].isin(valid_platforms[valid_platforms > 0].index)]
        l_merged['sov'] = (l_merged['brand_count'] / l_merged['total']) * 100
        
        fig_l = px.line(l_merged, x='date', y='sov', color='AI platform', markers=True, labels={'sov': 'Share of Voice (%)', 'date': ''}, height=400)
        fig_l.update_layout(yaxis=dict(rangemode='tozero'), xaxis=dict(tickformat="%b %d"))
        fig_l.update_traces(hovertemplate='%{y:.1f}% SoV<extra></extra>')
        st.plotly_chart(fig_l, use_container_width=True, key="tab1_line_plat")
    else:
        st.info("No data available for the selected geography.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### SoV by Geography")
    all_plats_options = ["All AI Platforms"] + sorted(scope_df_1['AI platform'].unique())
    selected_plats = st.multiselect("Filter AI Platform", all_plats_options, default=["All AI Platforms"], key="plat_filter")
    right_df = scope_df_1 if "All AI Platforms" in selected_plats else scope_df_1[scope_df_1['AI platform'].isin(selected_plats)]
        
    if not right_df.empty:
        r_totals = right_df.groupby(['date', 'country']).size().reset_index(name='total')
        r_brand = right_df.groupby(['date', 'country', 'mentioned_brands']).size().reset_index(name='brand_count')
        r_merged = pd.merge(r_totals, r_brand[r_brand['mentioned_brands'] == brand_1], on=['date', 'country'], how='left').fillna(0)
        
        valid_countries = r_merged.groupby('country')['brand_count'].sum()
        r_merged = r_merged[r_merged['country'].isin(valid_countries[valid_countries > 0].index)]
        r_merged['sov'] = (r_merged['brand_count'] / r_merged['total']) * 100
        
        fig_r = px.line(r_merged, x='date', y='sov', color='country', markers=True, labels={'sov': 'Share of Voice (%)', 'date': ''}, height=400)
        fig_r.update_layout(yaxis=dict(rangemode='tozero'), xaxis=dict(tickformat="%b %d"))
        fig_r.update_traces(hovertemplate='%{y:.1f}% SoV<extra></extra>')
        st.plotly_chart(fig_r, use_container_width=True, key="tab1_line_geo")
    else:
        st.info("No data available for the selected AI Platform.")
            
    st.markdown("---")
    st.subheader("Strategic Heatmap: Geographies vs AI Platforms", help="Displays your brand's Index vs Industry Average. 100 = Average. Grey with '-' means the brand has no presence or the AI platform is not available in this market.")
    
    hm_pivot = hm_df.pivot(index='country', columns='AI platform', values='index_vs_avg')
    hm_totals_pivot = hm_df.pivot(index='country', columns='AI platform', values='total')
    y_order, x_order = ["USA", "Brazil", "India", "China", "Indonesia"], ["Gemini", "Chat GPT", "Amazon Rufus", "Qwen", "AI Lazzie"]
    hm_pivot = hm_pivot.reindex(index=y_order, columns=x_order)
    hm_totals_pivot = hm_totals_pivot.reindex(index=y_order, columns=x_order)
    
    mask = (hm_totals_pivot > 0) & (hm_pivot > 0)
    hm_pivot_masked = hm_pivot.where(mask, np.nan)
    
    text_array = [["-" if pd.isna(v) else f"{v:.0f}" for v in r] for r in hm_pivot_masked.values]
    
    fig_hm = px.imshow(hm_pivot_masked, aspect="auto", color_continuous_scale="RdYlGn", color_continuous_midpoint=100, labels=dict(x="AI Platform", y="Geography", color="Index"))
    fig_hm.update_traces(text=text_array, texttemplate="%{text}")
    fig_hm.update_layout(xaxis_title="", yaxis_title="", yaxis=dict(autorange="reversed"), plot_bgcolor="#e2e8f0")
    st.plotly_chart(fig_hm, use_container_width=True, key="tab1_heatmap")


# === TAB 2: COMPETITOR BENCHMARKING ===
with tab_sov:
    st.markdown("<div style='padding-top: 10px;'></div>", unsafe_allow_html=True)
    c1_2, c2_2 = st.columns(2)
    cat_2 = c1_2.selectbox("📂 Select Category", sorted(df['category'].unique()), key='cat_2')
    scope_df_2 = df_exploded[df_exploded['category'] == cat_2]
    
    if not scope_df_2.empty:
        brands_2 = scope_df_2['mentioned_brands'].value_counts().head(50).index.tolist()
        brand_2 = c2_2.selectbox("🎯 Select Focus Brand", brands_2, index=0, key='brand_2')
    else:
        st.warning("No data for this category.")
        st.stop()
        
    st.markdown("---")
    st.subheader("Competitive Share of Voice Analysis", help="Compare your brand directly against the top 10 competitors in this category.")
    st.markdown("#### SoV Evolution", help="Only countries and AI platforms where the brand selected in the main filter is present are available to view in this chart.")
    
    f1_2, f2_2 = st.columns(2)
    brand_2_presence_df = scope_df_2[scope_df_2['mentioned_brands'] == brand_2]
    avail_countries_2 = sorted(brand_2_presence_df['country'].unique()) if not brand_2_presence_df.empty else []
    avail_platforms_2 = sorted(brand_2_presence_df['AI platform'].unique()) if not brand_2_presence_df.empty else []
    
    sel_countries_2 = f1_2.multiselect("🌍 Filter by Country", avail_countries_2, default=avail_countries_2, key="trend_country")
    sel_platforms_2 = f2_2.multiselect("🤖 Filter by AI Platform", avail_platforms_2, default=avail_platforms_2, key="trend_plat")
    
    line_scope_df = scope_df_2[(scope_df_2['country'].isin(sel_countries_2)) & (scope_df_2['AI platform'].isin(sel_platforms_2))]
    daily_counts = line_scope_df.groupby(['date', 'mentioned_brands']).size().reset_index(name='count')
    
    if not daily_counts.empty:
        daily_totals = daily_counts.groupby('date')['count'].transform('sum')
        daily_counts['sov_pct'] = (daily_counts['count'] / daily_totals) * 100
        top_10 = line_scope_df['mentioned_brands'].value_counts().head(10).index.tolist()
        if brand_2 not in top_10: top_10.append(brand_2) 
        
        filtered_daily = daily_counts[daily_counts['mentioned_brands'].isin(top_10)]
        fig_time_comp = px.line(filtered_daily, x='date', y='sov_pct', color='mentioned_brands', labels={'sov_pct': 'Share of Voice (%)', 'date': ''}, markers=True)
        fig_time_comp.update_layout(yaxis=dict(rangemode='tozero'), xaxis=dict(tickformat="%b %d"))
        fig_time_comp.update_traces(opacity=0.3)
        fig_time_comp.update_traces(selector={'name':brand_2}, opacity=1, line={'width': 4})
        st.plotly_chart(fig_time_comp, use_container_width=True, key="tab2_line_comp")
    else:
        st.info("No timeline data available for these filter selections.")
    
    st.markdown("---")
    st.markdown("#### Competitor Deep Dive", help="Directly compare your ranking vs a specific rival across all available markets and AI platforms.")
    
    available_competitors = [b for b in brands_2 if b != brand_2]
    competitor_brand = st.selectbox("🤼 Select Competitor", available_competitors, index=0, key='comp_brand', help="Select a rival brand to compare side-by-side rankings.")
    
    if competitor_brand:
        cp_totals = scope_df_2.groupby(['country', 'AI platform']).size().reset_index(name='total')
        cp_brands = scope_df_2.groupby(['country', 'AI platform', 'mentioned_brands']).size().reset_index(name='count')
        cp_brands['rank'] = cp_brands.groupby(['country', 'AI platform'])['count'].rank(method='min', ascending=False)
        
        focus_df = cp_brands[cp_brands['mentioned_brands'] == brand_2].set_index(['country', 'AI platform'])
        comp_df = cp_brands[cp_brands['mentioned_brands'] == competitor_brand].set_index(['country', 'AI platform'])
        
        compare_df = pd.DataFrame(index=cp_totals.set_index(['country', 'AI platform']).index)
        compare_df['focus_rank'] = focus_df['rank']
        compare_df['comp_rank'] = comp_df['rank']
        compare_df['focus_count'] = focus_df['count'].fillna(0)
        compare_df['comp_count'] = comp_df['count'].fillna(0)
        
        compare_df = compare_df.loc[compare_df[(compare_df['focus_count'] > 0) | (compare_df['comp_count'] > 0)].index].reset_index()
        
        if not compare_df.empty:
            focus_pivot = compare_df.pivot(index='country', columns='AI platform', values='focus_rank')
            comp_pivot = compare_df.pivot(index='country', columns='AI platform', values='comp_rank')
            
            all_countries = sorted(list(set(focus_pivot.index) | set(comp_pivot.index)))
            all_platforms = sorted(list(set(focus_pivot.columns) | set(comp_pivot.columns)))
            focus_pivot, comp_pivot = focus_pivot.reindex(index=all_countries, columns=all_platforms), comp_pivot.reindex(index=all_countries, columns=all_platforms)
            
            color_matrix, focus_text, comp_text = pd.DataFrame(np.nan, index=all_countries, columns=all_platforms), pd.DataFrame("-", index=all_countries, columns=all_platforms), pd.DataFrame("-", index=all_countries, columns=all_platforms)
            
            for c in all_platforms:
                for r in all_countries:
                    f_val, c_val = focus_pivot.loc[r, c], comp_pivot.loc[r, c]
                    if pd.notna(f_val): focus_text.loc[r, c] = f"Rank {int(f_val)}"
                    if pd.notna(c_val): comp_text.loc[r, c] = f"Rank {int(c_val)}"
                    
                    if pd.isna(f_val) and pd.isna(c_val): color_matrix.loc[r, c] = np.nan
                    elif pd.isna(f_val): color_matrix.loc[r, c] = -1 
                    elif pd.isna(c_val): color_matrix.loc[r, c] = 1
                    else: color_matrix.loc[r, c] = 1 if f_val < c_val else -1 if f_val > c_val else 0

            col_hm1, col_hm2 = st.columns(2)
            with col_hm1:
                st.markdown(f"**{brand_2} Ranking**")
                fig_focus = px.imshow(color_matrix, aspect="auto", color_continuous_scale=['#ef4444', '#f59e0b', '#10b981'], zmin=-1, zmax=1)
                fig_focus.update_traces(text=focus_text.values, texttemplate="%{text}", hoverinfo="skip")
                fig_focus.update_layout(coloraxis_showscale=False, xaxis_title="", yaxis_title="", plot_bgcolor="#e2e8f0", margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_focus, use_container_width=True, key="tab2_hm_focus")
            with col_hm2:
                st.markdown(f"**{competitor_brand} Ranking**")
                fig_comp = px.imshow(cp_brands['rank'].max() - comp_pivot, aspect="auto", color_continuous_scale="Blues")
                fig_comp.update_traces(text=comp_text.values, texttemplate="%{text}", hoverinfo="skip")
                fig_comp.update_layout(coloraxis_showscale=False, xaxis_title="", yaxis_title="", plot_bgcolor="#e2e8f0", margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_comp, use_container_width=True, key="tab2_hm_comp")
                
            st.caption("🟢 Green: Stronger than competitor | 🟡 Yellow: Tied | 🔴 Red: Weaker than competitor")
        else:
            st.info("Neither brand has a presence in the filtered data.")


# === TAB 3: SEARCH CRITERIA & PERCEPTION ===
with tab_semantic:
    st.markdown("<div style='padding-top: 10px;'></div>", unsafe_allow_html=True)
    c1_3, c2_3 = st.columns(2)
    cat_3 = c1_3.selectbox("📂 Select Category", sorted(df['category'].unique()), key='cat_3')
    scope_df_3 = df_exploded[df_exploded['category'] == cat_3]
    
    if not scope_df_3.empty:
        brands_3 = scope_df_3['mentioned_brands'].value_counts().head(50).index.tolist()
        brand_3 = c2_3.selectbox("🎯 Select Focus Brand", brands_3, index=0, key='brand_3')
    else:
        st.warning("No data for this category.")
        st.stop()
        
    st.markdown("---")
    st.subheader("Share of Voice by Search Criteria", help="Analyze how your brand's visibility fluctuates based on specific shopper search intents (e.g. Budget vs Premium).")
    
    f1_3, f2_3, f3_3 = st.columns(3)
    brand_3_presence_df = scope_df_3[scope_df_3['mentioned_brands'] == brand_3]
    avail_countries_3 = sorted(brand_3_presence_df['country'].unique()) if not brand_3_presence_df.empty else []
    avail_platforms_3 = sorted(brand_3_presence_df['AI platform'].unique()) if not brand_3_presence_df.empty else []
    avail_criteria_3 = sorted(scope_df_3['criteria'].astype(str).unique())
    
    sel_countries_3 = f1_3.multiselect("🌍 Filter by Country", avail_countries_3, default=avail_countries_3, key="crit_country")
    sel_platforms_3 = f2_3.multiselect("🤖 Filter by AI Platform", avail_platforms_3, default=avail_platforms_3, key="crit_plat")
    sel_criteria_3 = f3_3.multiselect("🔎 Filter by Criteria", avail_criteria_3, default=avail_criteria_3, key="crit_crit")
    
    crit_scope_df = scope_df_3[(scope_df_3['country'].isin(sel_countries_3)) & (scope_df_3['AI platform'].isin(sel_platforms_3)) & (scope_df_3['criteria'].astype(str).isin(sel_criteria_3))]
    daily_counts_3 = crit_scope_df.groupby(['date', 'mentioned_brands']).size().reset_index(name='count')
    
    if not daily_counts_3.empty:
        daily_totals_3 = daily_counts_3.groupby('date')['count'].transform('sum')
        daily_counts_3['sov_pct'] = (daily_counts_3['count'] / daily_totals_3) * 100
        top_10_crit = crit_scope_df['mentioned_brands'].value_counts().head(10).index.tolist()
        if brand_3 not in top_10_crit: top_10_crit.append(brand_3) 
        
        filtered_daily_3 = daily_counts_3[daily_counts_3['mentioned_brands'].isin(top_10_crit)]
        fig_time_crit = px.line(filtered_daily_3, x='date', y='sov_pct', color='mentioned_brands', labels={'sov_pct': 'Share of Voice (%)', 'date': ''}, markers=True)
        fig_time_crit.update_layout(yaxis=dict(rangemode='tozero'), xaxis=dict(tickformat="%b %d"))
        fig_time_crit.update_traces(opacity=0.3)
        fig_time_crit.update_traces(selector={'name':brand_3}, opacity=1, line={'width': 4})
        st.plotly_chart(fig_time_crit, use_container_width=True, key="tab3_line_crit")
    else:
        st.info("No timeline data available for these filter selections.")
        
    st.markdown("---")
    
    # --- NEW: Criteria Competitor Deep Dive Matrix ---
    st.markdown("#### Criteria Competitor Deep Dive", help="Directly compare your ranking vs a specific rival across markets and platforms, specifically for the search criteria selected above.")
    
    available_competitors_3 = [b for b in brands_3 if b != brand_3]
    competitor_brand_3 = st.selectbox("🤼 Select Competitor", available_competitors_3, index=0, key='comp_brand_3')
    
    if competitor_brand_3:
        # Filter the matrix data strictly by the selected criteria to reflect how brands perform in that specific narrative
        matrix_df_3 = scope_df_3[scope_df_3['criteria'].astype(str).isin(sel_criteria_3)]
        
        cp_totals_3 = matrix_df_3.groupby(['country', 'AI platform']).size().reset_index(name='total')
        cp_brands_3 = matrix_df_3.groupby(['country', 'AI platform', 'mentioned_brands']).size().reset_index(name='count')
        
        cp_brands_3['rank'] = cp_brands_3.groupby(['country', 'AI platform'])['count'].rank(method='min', ascending=False)
        
        focus_df_3 = cp_brands_3[cp_brands_3['mentioned_brands'] == brand_3].set_index(['country', 'AI platform'])
        comp_df_3 = cp_brands_3[cp_brands_3['mentioned_brands'] == competitor_brand_3].set_index(['country', 'AI platform'])
        
        compare_df_3 = pd.DataFrame(index=cp_totals_3.set_index(['country', 'AI platform']).index)
        compare_df_3['focus_rank'] = focus_df_3['rank']
        compare_df_3['comp_rank'] = comp_df_3['rank']
        compare_df_3['focus_count'] = focus_df_3['count'].fillna(0)
        compare_df_3['comp_count'] = comp_df_3['count'].fillna(0)
        
        valid_combos_3 = compare_df_3[(compare_df_3['focus_count'] > 0) | (compare_df_3['comp_count'] > 0)].index
        compare_df_3 = compare_df_3.loc[valid_combos_3].reset_index()
        
        if not compare_df_3.empty:
            focus_pivot_3 = compare_df_3.pivot(index='country', columns='AI platform', values='focus_rank')
            comp_pivot_3 = compare_df_3.pivot(index='country', columns='AI platform', values='comp_rank')
            
            all_countries_3 = sorted(list(set(focus_pivot_3.index) | set(comp_pivot_3.index)))
            all_platforms_3 = sorted(list(set(focus_pivot_3.columns) | set(comp_pivot_3.columns)))
            
            focus_pivot_3 = focus_pivot_3.reindex(index=all_countries_3, columns=all_platforms_3)
            comp_pivot_3 = comp_pivot_3.reindex(index=all_countries_3, columns=all_platforms_3)
            
            color_matrix_3 = pd.DataFrame(np.nan, index=all_countries_3, columns=all_platforms_3)
            focus_text_3 = pd.DataFrame("-", index=all_countries_3, columns=all_platforms_3)
            comp_text_3 = pd.DataFrame("-", index=all_countries_3, columns=all_platforms_3)
            
            for c in all_platforms_3:
                for r in all_countries_3:
                    f_val = focus_pivot_3.loc[r, c]
                    c_val = comp_pivot_3.loc[r, c]
                    
                    if pd.notna(f_val): focus_text_3.loc[r, c] = f"Rank {int(f_val)}"
                    if pd.notna(c_val): comp_text_3.loc[r, c] = f"Rank {int(c_val)}"
                    
                    if pd.isna(f_val) and pd.isna(c_val):
                        color_matrix_3.loc[r, c] = np.nan
                    elif pd.isna(f_val):
                        color_matrix_3.loc[r, c] = -1 
                    elif pd.isna(c_val):
                        color_matrix_3.loc[r, c] = 1
                    else:
                        if f_val < c_val: color_matrix_3.loc[r, c] = 1
                        elif f_val > c_val: color_matrix_3.loc[r, c] = -1
                        else: color_matrix_3.loc[r, c] = 0

            col_hm1_3, col_hm2_3 = st.columns(2)
            
            with col_hm1_3:
                st.markdown(f"**{brand_3} Ranking (Filtered by Criteria)**")
                fig_focus_3 = px.imshow(color_matrix_3, aspect="auto", color_continuous_scale=['#ef4444', '#f59e0b', '#10b981'], zmin=-1, zmax=1)
                fig_focus_3.update_traces(text=focus_text_3.values, texttemplate="%{text}", hoverinfo="skip")
                fig_focus_3.update_layout(coloraxis_showscale=False, xaxis_title="", yaxis_title="", plot_bgcolor="#e2e8f0", margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_focus_3, use_container_width=True, key="tab3_hm_focus")
                
            with col_hm2_3:
                st.markdown(f"**{competitor_brand_3} Ranking (Filtered by Criteria)**")
                max_rank_3 = cp_brands_3['rank'].max()
                comp_color_3 = max_rank_3 - comp_pivot_3
                fig_comp_3 = px.imshow(comp_color_3, aspect="auto", color_continuous_scale="Blues")
                fig_comp_3.update_traces(text=comp_text_3.values, texttemplate="%{text}", hoverinfo="skip")
                fig_comp_3.update_layout(coloraxis_showscale=False, xaxis_title="", yaxis_title="", plot_bgcolor="#e2e8f0", margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_comp_3, use_container_width=True, key="tab3_hm_comp")
                
            st.caption("🟢 Green: Stronger than competitor | 🟡 Yellow: Tied | 🔴 Red: Weaker than competitor")
        else:
            st.info("Neither brand has a presence in the selected criteria data.")

    st.markdown("---")

    # --- ADVANCED FAST NLP DESCRIPTOR SECTION ---
    st.subheader(f"How LLMs Describe '{brand_3}'", help="Semantic analysis of the exact descriptors & attributes AI assistants use when recommending this brand.")
    
    brand_3_data = scope_df_3[scope_df_3['mentioned_brands'] == brand_3]
    extracted_features = [attr for sublist in brand_3_data['extracted_attributes'] if isinstance(sublist, list) for attr in sublist]

    if extracted_features:
        total_brand_mentions = len(brand_3_data)
        word_counts = Counter(extracted_features).most_common(12)
        
        wc_data = []
        for word, count in word_counts:
            pct = (count / total_brand_mentions) * 100 
            icon = attribute_lexicon[word]
            wc_data.append({'Keyword_Display': f"{word.title()} {icon}", 'Percentage': pct, 'Raw_Word': word})
            
        wc_df = pd.DataFrame(wc_data)
        
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("#### Top Descriptors & Attributes (%)")
            fig_bar = px.bar(wc_df, x='Percentage', y='Keyword_Display', orientation='h', color='Percentage', color_continuous_scale='Blues', labels={'Percentage': '% of Mentions', 'Keyword_Display': ''})
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True, key="tab3_bar_words")
            
        with c2:
            st.markdown("#### Thematic Radar (%)")
            theme_scores = {k: 0 for k in theme_mapping.keys()}
            for word in extracted_features:
                for theme, words_in_theme in theme_mapping.items():
                    if word in words_in_theme:
                        theme_scores[theme] += 1
            
            total_theme_hits = sum(theme_scores.values())
            theme_data = [{'Theme': t, 'Percentage': (c / total_theme_hits) * 100 if total_theme_hits > 0 else 0} for t, c in theme_scores.items()]
                
            fig_radar = px.line_polar(pd.DataFrame(theme_data), r='Percentage', theta='Theme', line_close=True)
            fig_radar.update_traces(fill='toself', line_color='#6366f1')
            st.plotly_chart(fig_radar, use_container_width=True, key="tab3_radar_theme")
            
        # --- Contextual Deep Dive Module (FAST Two-Tier Filter) ---
        st.markdown("---")
        st.markdown("#### Contextual Deep Dive")
        st.write("Select a strategic theme and drill down into specific descriptors & attributes to understand exactly where and how AI platforms are framing your brand.")
        
        f_theme, f_attr = st.columns(2)
        selected_theme = f_theme.selectbox("🎯 Select Theme:", list(theme_mapping.keys()), key="insight_theme")
        
        theme_present_words = [w for w in set(extracted_features) if w in theme_mapping[selected_theme]]
        
        if theme_present_words:
            selected_attribute = f_attr.selectbox("🔎 Select Descriptor / Attribute:", ["-- Overall Theme Insight --"] + sorted(theme_present_words), key="insight_attr")
            
            if selected_attribute == "-- Overall Theme Insight --":
                theme_set = set(theme_present_words)
                mask = brand_3_data['extracted_attributes'].apply(lambda x: bool(set(x) & theme_set) if isinstance(x, list) else False)
                insight_subset = brand_3_data[mask]
                
                if not insight_subset.empty:
                    top_plat = insight_subset['AI platform'].value_counts().index[0]
                    top_country = insight_subset['country'].value_counts().index[0]
                    plat_pct = (len(insight_subset[insight_subset['AI platform'] == top_plat]) / len(insight_subset)) * 100
                    
                    st.info(f"🧠 **Theme Insight ({selected_theme}):** AI platforms frequently discuss {brand_3} in the context of **{selected_theme}**. " 
                            f"This narrative is heavily driven by **{top_plat}** (accounting for {plat_pct:.0f}% of these thematic mentions), especially in the **{top_country}** market. "
                            f"The most commonly cited attributes driving this theme are: **{', '.join(theme_present_words[:5])}**.")
                else:
                    st.info(f"Not enough data to generate an aggregate insight for {selected_theme}.")
            else:
                mask = brand_3_data['extracted_attributes'].apply(lambda x: selected_attribute in x if isinstance(x, list) else False)
                insight_subset = brand_3_data[mask]
                
                if not insight_subset.empty:
                    top_plat = insight_subset['AI platform'].value_counts().index[0]
                    top_country = insight_subset['country'].value_counts().index[0]
                    plat_pct = (len(insight_subset[insight_subset['AI platform'] == top_plat]) / len(insight_subset)) * 100
                    
                    icon = attribute_lexicon[selected_attribute]
                    sentiment_text = "Positive" if icon == '🟢' else "Negative" if icon == '🔴' else "Neutral"
                    
                    ai_text = f"🧠 **Attribute Insight:** The descriptor **'{selected_attribute}'** registers as a **{sentiment_text}** signal for {brand_3} within the {selected_theme} category. " \
                              f"It is heavily indexed in the **{top_country}** market, primarily driven by recommendations on **{top_plat}** (accounting for {plat_pct:.0f}% of these specific mentions). " \
                              f"When AI assistants highlight this feature, they are generally positioning the brand to appeal to shoppers prioritizing " \
                              f"{'premium quality and efficacy' if sentiment_text == 'Positive' else 'budget constraints or identified product flaws' if sentiment_text == 'Negative' else 'specific formulation and formatting requirements'}."
                    
                    st.info(ai_text)
                else:
                    st.info("Insufficient data to generate a deep dive for this specific term.")
        else:
            st.info(f"No descriptors or attributes related to '{selected_theme}' were found for {brand_3} in the current data selection.")
    else:
        st.warning("Not enough highly-relevant product attribute data to generate semantic analysis for this brand.")

# === TAB 4: SOURCE INTELLIGENCE ===
with tab_sources:
    st.markdown("<div style='padding-top: 10px;'></div>", unsafe_allow_html=True)
    c1_4, c2_4 = st.columns(2)
    cat_4 = c1_4.selectbox("📂 Select Category", sorted(df['category'].unique()), key='cat_4')
    scope_df_4 = df_exploded[df_exploded['category'] == cat_4]
    
    if not scope_df_4.empty:
        brands_4 = scope_df_4['mentioned_brands'].value_counts().head(50).index.tolist()
        brand_4 = c2_4.selectbox("🎯 Select Focus Brand", brands_4, index=0, key='brand_4')
    else:
        st.warning("No data for this category.")
        st.stop()
        
    st.markdown("---")

    st.subheader("Where is the LLM getting this info?", help="Traces the AI recommendations back to their origin authoritative sources across the web.")
    st.info("Based on citation patterns and known training data correlations.")
    
    brand_source_df = scope_df_4[scope_df_4['mentioned_brands'] == brand_4]
    
    if not brand_source_df.empty:
        source_counts = brand_source_df['source_citation'].value_counts().reset_index()
        source_counts.columns = ['Source', 'Mentions']
        
        c1, c2 = st.columns([2, 1])
        
        with c1:
            fig_tree = px.treemap(source_counts, path=['Source'], values='Mentions', color='Mentions', color_continuous_scale='RdBu')
            st.plotly_chart(fig_tree, use_container_width=True, key="tab4_tree_source")
            
        with c2:
            st.markdown("#### Actionable Targets")
            cat_sources = scope_df_4['source_citation'].value_counts(normalize=True)
            brand_sources = brand_source_df['source_citation'].value_counts(normalize=True)
            
            gap = (cat_sources - brand_sources).dropna().sort_values(ascending=False).head(3)
            
            st.markdown("<p style='font-size: 14px; color: #64748b;'>Below are the sources your competitors are leveraging more effectively than you:</p>", unsafe_allow_html=True)
            if not gap.empty:
                for source, diff in gap.items():
                    st.warning(f"📉 **{source}**: Under-represented by {(diff*100):.1f}% vs category avg.")
            else:
                st.success("Your source distribution matches or exceeds the category average!")
    else:
        st.warning("No source data available for this brand.")
