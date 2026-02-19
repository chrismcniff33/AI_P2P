import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import random
from collections import Counter

# --- 1. PAGE CONFIGURATION & STYLING ---
st.set_page_config(page_title="BrandAI: Strategic Intelligence", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
        .block-container {padding-top: 1rem; padding-bottom: 2rem;}
        h1 {color: #1e293b; font-family: 'Helvetica Neue', sans-serif;}
        .metric-card {background-color: #f8fafc; padding: 20px; border-radius: 8px; border-left: 5px solid #6366f1;}
        div[data-testid="stMetricValue"] {font-size: 1.5rem; color: #4F46E5;}
        .stTabs [data-baseweb="tab-list"] {gap: 10px; border-bottom: 1px solid #e5e7eb;}
        .stTabs [data-baseweb="tab"] {height: 50px; white-space: pre-wrap; background-color: #f1f5f9; border-radius: 5px 5px 0px 0px; padding: 10px 20px;}
        .stTabs [aria-selected="true"] {background-color: #4f46e5; color: white;}
    </style>
""", unsafe_allow_html=True)

# --- 2. PASSWORD PROTECTION ---
def check_password():
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

# --- 4. SIDEBAR (Scope Only) ---
with st.sidebar:
    st.title("🚀 BrandAI")
    st.subheader("Define Market Scope")
    selected_category = st.selectbox("Category", sorted(df['category'].unique()))
    avail_countries = sorted(df[df['category'] == selected_category]['country'].unique())
    selected_country = st.selectbox("Market (Country)", ["All"] + avail_countries)
    
    scope_df = df_exploded[df_exploded['category'] == selected_category]
    if selected_country != "All":
        scope_df = scope_df[scope_df['country'] == selected_country]
    
    st.markdown("---")
    st.info(f"Analyzing {len(scope_df):,} mentions.")

# --- 5. TOP LEVEL BRAND FILTER ---
st.title("Strategic Brand Intelligence")

if not scope_df.empty:
    available_brands = scope_df['mentioned_brands'].value_counts().head(50).index.tolist()
    target_brand = st.selectbox("🎯 Select Focus Brand", available_brands, index=0)
else:
    st.warning("No data for this category/market selection.")
    st.stop()

st.markdown("<br>", unsafe_allow_html=True)

# --- 6. MAIN TABS ---
tab_insight, tab_sov, tab_semantic, tab_sources = st.tabs([
    "👁️ AI Visibility Overview", 
    "📊 Share of Voice Trends", 
    "💬 Brand Perception", 
    "🔗 Source Intelligence"
])

# === TAB 1: AI VISIBILITY OVERVIEW (REDESIGNED) ===
with tab_insight:
    
    # --- INFOGRAPHICS ROW ---
    st.markdown("### Global AI Visibility Metrics")
    
    # Math for Infographics
    global_mentions = len(scope_df)
    brand_mentions = len(scope_df[scope_df['mentioned_brands'] == target_brand])
    global_sov = (brand_mentions / global_mentions) * 100 if global_mentions > 0 else 0
    
    num_brands = len(scope_df['mentioned_brands'].unique())
    ind_avg_sov = 100.0 / num_brands if num_brands > 0 else 0
    
    ratio = global_sov / ind_avg_sov if ind_avg_sov > 0 else 0
    if ratio < 0.5: visibility = "Low 🔴"
    elif ratio < 0.8: visibility = "Moderate 🟠"
    elif ratio < 1.2: visibility = "Average 🟡"
    elif ratio < 2.0: visibility = "Good 🟢"
    else: visibility = "Excellent 🌟"
    
    leader = scope_df['mentioned_brands'].value_counts().index[0]
    
    # Calculate Strengths / Weaknesses
    crit_counts = scope_df.groupby(['criteria', 'mentioned_brands']).size().unstack(fill_value=0)
    if not crit_counts.empty and target_brand in crit_counts.columns:
        crit_pct = crit_counts.div(crit_counts.sum(axis=1), axis=0) * 100
        top_strength = f"{crit_pct[target_brand].idxmax()} ({crit_pct[target_brand].max():.1f}%)"
        top_weakness = f"{crit_pct[target_brand].idxmin()} ({crit_pct[target_brand].min():.1f}%)"
    else:
        top_strength, top_weakness = "N/A", "N/A"

    # Display KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Visibility vs Industry", visibility, f"SoV: {global_sov:.1f}% (Avg: {ind_avg_sov:.1f}%)")
    col2.metric("Category Leader", leader)
    col3.metric("Top Strength (Criteria)", top_strength.split(" (")[0])
    col4.metric("Key Area for Improvement", top_weakness.split(" (")[0])

    st.markdown("---")
    
    # --- LINE CHARTS ROW ---
    st.markdown("### Cross-Segment Share of Voice Over Time")
    
    c_left, c_right = st.columns(2)
    
    with c_left:
        st.markdown("**SoV by AI Platform**")
        # Multiselect Filter for Geographies
        all_geos = sorted(scope_df['country'].unique())
        selected_geos = st.multiselect("Filter Geography", all_geos, default=all_geos, key="geo_filter")
        
        # Calculate Data
        left_df = scope_df[scope_df['country'].isin(selected_geos)]
        if not left_df.empty:
            l_totals = left_df.groupby(['date', 'AI platform']).size().reset_index(name='total')
            l_brand = left_df[left_df['mentioned_brands'] == target_brand].groupby(['date', 'AI platform']).size().reset_index(name='brand_count')
            l_merged = pd.merge(l_totals, l_brand, on=['date', 'AI platform'], how='left').fillna(0)
            l_merged['sov'] = (l_merged['brand_count'] / l_merged['total']) * 100
            
            fig_l = px.line(l_merged, x='date', y='sov', color='AI platform', markers=True, 
                            labels={'sov': 'Share of Voice (%)'}, title=f"{target_brand} Visibility by AI Platform")
            
            # Add Industry Average Line (Dashed)
            fig_l.add_hline(y=ind_avg_sov, line_dash="dash", line_color="gray", annotation_text="Industry Avg", annotation_position="bottom right")
            fig_l.update_traces(mode="lines+markers", hovertemplate='%{y:.1f}% SoV<extra></extra>')
            st.plotly_chart(fig_l, use_container_width=True)
        else:
            st.info("Please select at least one geography.")

    with c_right:
        st.markdown("**SoV by Geography**")
        # Multiselect Filter for AI Platforms
        all_plats = sorted(scope_df['AI platform'].unique())
        selected_plats = st.multiselect("Filter AI Platform", all_plats, default=all_plats, key="plat_filter")
        
        # Calculate Data
        right_df = scope_df[scope_df['AI platform'].isin(selected_plats)]
        if not right_df.empty:
            r_totals = right_df.groupby(['date', 'country']).size().reset_index(name='total')
            r_brand = right_df[right_df['mentioned_brands'] == target_brand].groupby(['date', 'country']).size().reset_index(name='brand_count')
            r_merged = pd.merge(r_totals, r_brand, on=['date', 'country'], how='left').fillna(0)
            r_merged['sov'] = (r_merged['brand_count'] / r_merged['total']) * 100
            
            fig_r = px.line(r_merged, x='date', y='sov', color='country', markers=True,
                            labels={'sov': 'Share of Voice (%)'}, title=f"{target_brand} Visibility by Country")
            
            # Add Industry Average Line (Dashed)
            fig_r.add_hline(y=ind_avg_sov, line_dash="dash", line_color="gray", annotation_text="Industry Avg", annotation_position="bottom right")
            fig_r.update_traces(mode="lines+markers", hovertemplate='%{y:.1f}% SoV<extra></extra>')
            st.plotly_chart(fig_r, use_container_width=True)
        else:
            st.info("Please select at least one AI Platform.")
            
    st.markdown("---")
    
    # --- HEATMAP MATRIX ---
    st.markdown("### Strategic Heatmap: Geographies vs AI Platforms")
    st.caption("Shows Index vs Average (100 = Industry Average). Dark green = Strong competitive advantage. Dark red = Critical blind spot.")
    
    # Calculate Heatmap Data
    hm_totals = scope_df.groupby(['country', 'AI platform']).size().reset_index(name='total')
    hm_brand = scope_df[scope_df['mentioned_brands'] == target_brand].groupby(['country', 'AI platform']).size().reset_index(name='brand_count')
    hm_df = pd.merge(hm_totals, hm_brand, on=['country', 'AI platform'], how='left').fillna(0)
    hm_df['sov'] = (hm_df['brand_count'] / hm_df['total']) * 100
    
    # Dynamic industry average per cell
    hm_unique_brands = scope_df.groupby(['country', 'AI platform'])['mentioned_brands'].nunique().reset_index(name='unique_brands')
    hm_df = pd.merge(hm_df, hm_unique_brands, on=['country', 'AI platform'])
    hm_df['ind_avg'] = 100.0 / hm_df['unique_brands'].replace(0, 1) # prevent div/0
    
    # Calculate Index (Cap at 300 for cleaner color scaling if there are crazy outliers)
    hm_df['index_vs_avg'] = (hm_df['sov'] / hm_df['ind_avg']) * 100
    hm_df['index_vs_avg'] = hm_df['index_vs_avg'].fillna(0)
    
    hm_pivot = hm_df.pivot(index='country', columns='AI platform', values='index_vs_avg').fillna(0)
    
    if not hm_pivot.empty:
        # Create a red-yellow-green custom colorscale
        fig_hm = px.imshow(hm_pivot, 
                           text_auto=".0f", 
                           aspect="auto",
                           color_continuous_scale="RdYlGn",
                           color_continuous_midpoint=100, # 100 is exact average (yellow)
                           labels=dict(x="AI Platform", y="Geography", color="Index"))
        
        fig_hm.update_layout(xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_hm, use_container_width=True)
    else:
        st.warning("Insufficient data to generate Heatmap.")

# === TAB 2: SHARE OF VOICE (COMPETITIVE TRENDS) ===
with tab_sov:
    st.header("Competitive Share of Voice Analysis")
    st.subheader("1. SoV Evolution (Top 10 Brands)")
    
    daily_counts = scope_df.groupby(['date', 'mentioned_brands']).size().reset_index(name='count')
    
    if not daily_counts.empty:
        daily_totals = daily_counts.groupby('date')['count'].transform('sum')
        daily_counts['sov_pct'] = (daily_counts['count'] / daily_totals) * 100
        
        top_10 = scope_df['mentioned_brands'].value_counts().head(10).index.tolist()
        if target_brand not in top_10: top_10.append(target_brand) 
        
        filtered_daily = daily_counts[daily_counts['mentioned_brands'].isin(top_10)]
        
        fig_time = px.line(filtered_daily, x='date', y='sov_pct', color='mentioned_brands',
                           title="Top Brands Visibility % Over Time",
                           labels={'sov_pct': 'Share of Voice (%)'},
                           markers=True)
        
        fig_time.update_traces(opacity=0.3)
        fig_time.update_traces(selector={'name':target_brand}, opacity=1, line={'width': 4})
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.info("No timeline data available.")
    
    st.subheader("2. Platform Dominance (Top Brands)")
    plat_counts = scope_df.groupby(['AI platform', 'mentioned_brands']).size().reset_index(name='count')
    
    if not plat_counts.empty:
        if 'top_10' not in locals():
            top_10 = scope_df['mentioned_brands'].value_counts().head(10).index.tolist()
            
        plat_filtered = plat_counts[plat_counts['mentioned_brands'].isin(top_10)]
        
        fig_plat = px.bar(plat_filtered, x='AI platform', y='count', color='mentioned_brands',
                          title="Brand Mentions Split by Platform",
                          barmode='stack')
        st.plotly_chart(fig_plat, use_container_width=True)
    else:
        st.info("No platform data available.")

# === TAB 3: BRAND PERCEPTION (NLP) ===
with tab_semantic:
    st.header(f"How LLMs Describe '{target_brand}'")
    
    brand_responses = df[
        (df['category'] == selected_category) & 
        (df['response'].str.contains(target_brand, case=False, na=False))
    ]['response']
    
    stopwords = set(['the', 'and', 'is', 'to', 'in', 'of', 'for', 'with', 'a', 'it', 'this', 'that', 'brand', 'product', 'recommend', 'options', 'choice', 'popular', 'user', 'users', 'reviews', 'are', 'as', 'on'])
    
    all_words = []
    for resp in brand_responses:
        clean_text = re.sub(r'[^\w\s]', '', resp.lower())
        words = clean_text.split()
        filtered = [w for w in words if w not in stopwords and w != target_brand.lower()]
        all_words.extend(filtered)
        
    if all_words:
        word_counts = Counter(all_words).most_common(15)
        wc_df = pd.DataFrame(word_counts, columns=['Keyword', 'Frequency'])
        
        c1, c2 = st.columns([1, 1])
        
        with c1:
            st.subheader("Top Descriptors")
            fig_bar = px.bar(wc_df, x='Frequency', y='Keyword', orientation='h',
                             title=f"Most Common Words",
                             color='Frequency', color_continuous_scale='Blues')
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with c2:
            st.subheader("Thematic Analysis")
            themes = {
                "Performance": ["effective", "quality", "strong", "results", "works", "durable", "fast", "clean"],
                "Price/Value": ["cheap", "affordable", "value", "budget", "price", "expensive", "premium", "cost"],
                "Ingredients/Specs": ["organic", "natural", "ingredients", "specs", "features", "contains", "oil", "vitamin"],
                "Sentiment": ["love", "good", "great", "best", "bad", "poor", "excellent", "favorite"]
            }
            
            theme_scores = {k: 0 for k in themes.keys()}
            for w in all_words:
                for theme, keywords in themes.items():
                    if w in keywords:
                        theme_scores[theme] += 1
            
            theme_df = pd.DataFrame(list(theme_scores.items()), columns=['Theme', 'Count'])
            fig_radar = px.line_polar(theme_df, r='Count', theta='Theme', line_close=True,
                                      title="Thematic Positioning Radar")
            fig_radar.update_traces(fill='toself', line_color='#6366f1')
            st.plotly_chart(fig_radar, use_container_width=True)
    else:
        st.warning("Not enough data to generate semantic analysis for this brand.")

# === TAB 4: SOURCE INTELLIGENCE ===
with tab_sources:
    st.header("Where is the LLM getting this info?")
    st.info("Based on citation patterns and known training data correlations (Simulated).")
    
    brand_source_df = scope_df[scope_df['mentioned_brands'] == target_brand]
    
    if not brand_source_df.empty:
        source_counts = brand_source_df['source_citation'].value_counts().reset_index()
        source_counts.columns = ['Source', 'Mentions']
        
        c1, c2 = st.columns([2, 1])
        
        with c1:
            fig_tree = px.treemap(source_counts, path=['Source'], values='Mentions',
                                  title=f"Top Sources Driving Visibility",
                                  color='Mentions', color_continuous_scale='RdBu')
            st.plotly_chart(fig_tree, use_container_width=True)
            
        with c2:
            st.subheader("Actionable Targets")
            cat_sources = scope_df['source_citation'].value_counts(normalize=True)
            brand_sources = brand_source_df['source_citation'].value_counts(normalize=True)
            
            gap = (cat_sources - brand_sources).dropna().sort_values(ascending=False).head(3)
            
            if not gap.empty:
                for source, diff in gap.items():
                    st.warning(f"📉 **{source}**: Under-represented by {(diff*100):.1f}% vs category avg.")
            else:
                st.success("Your source distribution matches or exceeds the category average!")
    else:
        st.warning("No source data available for this brand.")
