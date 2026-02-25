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
        
        /* Styling the Radio button to act as a Navigation Ribbon */
        div.row-widget.stRadio > div {
            flex-direction: row;
            gap: 15px;
            background-color: #f1f5f9;
            padding: 10px 15px;
            border-radius: 8px;
            border-bottom: 2px solid #e5e7eb;
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
        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input("Please enter the company password to access this tool:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
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
st.title("AI Path to Purchase")

# The Navigation Ribbon (Directly below title)
nav_options = [
    "👁️ Share of Voice Overview", 
    "📊 Share of Voice Trends", 
    "💬 Brand Perception", 
    "🔗 Source Intelligence"
]
selected_tab = st.radio("Navigation", nav_options, horizontal=True, label_visibility="collapsed")

st.markdown("<br>", unsafe_allow_html=True)

# The Filters (Directly below ribbon)
col_cat, col_brand = st.columns(2)

with col_cat:
    selected_category = st.selectbox("📂 Select Category", sorted(df['category'].unique()), help="Filter all dashboard metrics by specific product category")
    scope_df = df_exploded[df_exploded['category'] == selected_category]

with col_brand:
    if not scope_df.empty:
        available_brands = scope_df['mentioned_brands'].value_counts().head(50).index.tolist()
        target_brand = st.selectbox("🎯 Select Focus Brand", available_brands, index=0, help="Select the core brand to benchmark against the industry")
    else:
        st.warning("No data for this category.")
        st.stop()

st.markdown("---")

# --- 5. MAIN TAB LOGIC ---

# === TAB 1: SHARE OF VOICE OVERVIEW ===
if selected_tab == "👁️ Share of Voice Overview":
    
    st.subheader("Global AI Visibility Metrics", help="High-level summary of your brand's footprint across all monitored Generative AI platforms.")
    
    # Global Calculations
    global_mentions = len(scope_df)
    brand_mentions = len(scope_df[scope_df['mentioned_brands'] == target_brand])
    global_sov = (brand_mentions / global_mentions) * 100 if global_mentions > 0 else 0
    
    num_brands = len(scope_df['mentioned_brands'].unique())
    ind_avg_sov = 100.0 / num_brands if num_brands > 0 else 0
    
    ratio = global_sov / ind_avg_sov if ind_avg_sov > 0 else 0
    if ratio < 0.5: visibility = "Low"
    elif ratio < 0.8: visibility = "Moderate"
    elif ratio < 1.2: visibility = "Average"
    elif ratio < 2.0: visibility = "Good"
    else: visibility = "Excellent"
    
    # INTELLIGENT KPI CALCULATION (Linked to Heatmap Index Logic)
    hm_totals = scope_df.groupby(['country', 'AI platform']).size().reset_index(name='total')
    hm_brand = scope_df[scope_df['mentioned_brands'] == target_brand].groupby(['country', 'AI platform']).size().reset_index(name='brand_count')
    hm_unique = scope_df.groupby(['country', 'AI platform'])['mentioned_brands'].nunique().reset_index(name='unique_brands')
    
    hm_df = pd.merge(hm_totals, hm_brand, on=['country', 'AI platform'], how='left').fillna(0)
    hm_df = pd.merge(hm_df, hm_unique, on=['country', 'AI platform'])
    
    hm_df['sov'] = (hm_df['brand_count'] / hm_df['total']) * 100
    hm_df['ind_avg'] = 100.0 / hm_df['unique_brands'].replace(0, 1) 
    hm_df['index_vs_avg'] = (hm_df['sov'] / hm_df['ind_avg']) * 100
    
    # Filter to only places where category is active
    hm_valid = hm_df[hm_df['total'] > 0]
    
    if not hm_valid.empty and hm_valid['brand_count'].sum() > 0:
        idx_max = hm_valid['index_vs_avg'].idxmax()
        top_strength_str = f"{hm_valid.loc[idx_max, 'AI platform']} in {hm_valid.loc[idx_max, 'country']} 🏆"
        
        idx_min = hm_valid['index_vs_avg'].idxmin()
        top_weakness_str = f"{hm_valid.loc[idx_min, 'AI platform']} in {hm_valid.loc[idx_min, 'country']} ⚠️"
    else:
        top_strength_str = "N/A"
        top_weakness_str = "N/A"

    # Display 3 Equally Spaced Custom KPI Cards
    c1, c2, c3 = st.columns(3)
    
    # 1. Visibility Card (Color coded footer)
    footer_color = "#10b981" if visibility in ["Good", "Excellent"] else "#ef4444" if visibility == "Low" else "#f59e0b"
    c1.markdown(f"""
    <div class="custom-metric">
        <div style="color: #64748b; font-size: 14px; font-weight: 600;">Visibility vs Industry <span title="Your brand's overall Share of Voice compared to the average brand in this category">ℹ️</span></div>
        <div style="color: #4F46E5; font-size: 26px; font-weight: 700; margin-top: 5px;">{global_sov:.1f}%</div>
        <div style="color: {footer_color}; font-size: 14px; font-weight: 600; margin-top: 5px;">{visibility} (Avg: {ind_avg_sov:.1f}%)</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. Top Strength Card
    c2.markdown(f"""
    <div class="custom-metric">
        <div style="color: #64748b; font-size: 14px; font-weight: 600;">Top Strength <span title="The platform & market where your brand over-indexes the most vs competitors">ℹ️</span></div>
        <div style="color: #1e293b; font-size: 20px; font-weight: 700; margin-top: 10px; line-height: 1.2;">{top_strength_str}</div>
        <div style="color: #94a3b8; font-size: 13px; font-weight: 500; margin-top: 5px;">Based on Index vs Avg</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 3. Area for Improvement Card
    c3.markdown(f"""
    <div class="custom-metric">
        <div style="color: #64748b; font-size: 14px; font-weight: 600;">Area for Improvement <span title="The platform & market where your brand under-indexes the most vs competitors">ℹ️</span></div>
        <div style="color: #1e293b; font-size: 20px; font-weight: 700; margin-top: 10px; line-height: 1.2;">{top_weakness_str}</div>
        <div style="color: #94a3b8; font-size: 13px; font-weight: 500; margin-top: 5px;">Based on Index vs Avg</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- FULL WIDTH LINE CHARTS ---
    st.subheader("Cross-Segment Share of Voice Over Time", help="Tracks weekly fluctuations in AI recommendations to catch algorithmic shifts.")
    
    # CHART 1: SoV by AI Platform
    st.markdown("#### SoV by AI Platform")
    all_geos_options = ["Global"] + sorted(scope_df['country'].unique())
    selected_geos = st.multiselect("Filter Geography", all_geos_options, default=["Global"], key="geo_filter", help="Isolate the trendline data to specific countries.")
    
    if "Global" in selected_geos:
        left_df = scope_df
    else:
        left_df = scope_df[scope_df['country'].isin(selected_geos)]
        
    if not left_df.empty:
        l_totals = left_df.groupby(['date', 'AI platform']).size().reset_index(name='total')
        l_brand = left_df[left_df['mentioned_brands'] == target_brand].groupby(['date', 'AI platform']).size().reset_index(name='brand_count')
        l_merged = pd.merge(l_totals, l_brand, on=['date', 'AI platform'], how='left').fillna(0)
        l_merged['sov'] = (l_merged['brand_count'] / l_merged['total']) * 100
        
        fig_l = px.line(l_merged, x='date', y='sov', color='AI platform', markers=True, 
                        labels={'sov': 'Share of Voice (%)'}, height=400)
        
        # Moving Average Calculation for Industry Average
        ind_avg_df_l = left_df.groupby('date')['mentioned_brands'].nunique().reset_index(name='unique')
        ind_avg_df_l['daily_avg'] = 100.0 / ind_avg_df_l['unique'].replace(0, 1)
        ind_avg_df_l['ind_avg_ma'] = ind_avg_df_l['daily_avg'].rolling(window=3, min_periods=1).mean()
        
        fig_l.add_trace(go.Scatter(
            x=ind_avg_df_l['date'], y=ind_avg_df_l['ind_avg_ma'],
            mode='lines', line=dict(dash='dash', color='gray', width=2),
            name='Ind Moving Avg', hovertemplate='Moving Avg: %{y:.1f}%<extra></extra>'
        ))
        
        fig_l.update_traces(hovertemplate='%{y:.1f}% SoV<extra></extra>')
        st.plotly_chart(fig_l, use_container_width=True, help="Trendline of brand visibility separated by LLM platform.")
    else:
        st.info("No data available for the selected geography.")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # CHART 2: SoV by Geography
    st.markdown("#### SoV by Geography")
    all_plats_options = ["All AI Platforms"] + sorted(scope_df['AI platform'].unique())
    selected_plats = st.multiselect("Filter AI Platform", all_plats_options, default=["All AI Platforms"], key="plat_filter", help="Isolate the geographic trends to specific LLMs.")
    
    if "All AI Platforms" in selected_plats:
        right_df = scope_df
    else:
        right_df = scope_df[scope_df['AI platform'].isin(selected_plats)]
        
    if not right_df.empty:
        r_totals = right_df.groupby(['date', 'country']).size().reset_index(name='total')
        r_brand = right_df[right_df['mentioned_brands'] == target_brand].groupby(['date', 'country']).size().reset_index(name='brand_count')
        r_merged = pd.merge(r_totals, r_brand, on=['date', 'country'], how='left').fillna(0)
        r_merged['sov'] = (r_merged['brand_count'] / r_merged['total']) * 100
        
        fig_r = px.line(r_merged, x='date', y='sov', color='country', markers=True,
                        labels={'sov': 'Share of Voice (%)'}, height=400)
        
        # Moving Average Calculation
        ind_avg_df_r = right_df.groupby('date')['mentioned_brands'].nunique().reset_index(name='unique')
        ind_avg_df_r['daily_avg'] = 100.0 / ind_avg_df_r['unique'].replace(0, 1)
        ind_avg_df_r['ind_avg_ma'] = ind_avg_df_r['daily_avg'].rolling(window=3, min_periods=1).mean()
        
        fig_r.add_trace(go.Scatter(
            x=ind_avg_df_r['date'], y=ind_avg_df_r['ind_avg_ma'],
            mode='lines', line=dict(dash='dash', color='gray', width=2),
            name='Ind Moving Avg', hovertemplate='Moving Avg: %{y:.1f}%<extra></extra>'
        ))
        
        fig_r.update_traces(hovertemplate='%{y:.1f}% SoV<extra></extra>')
        st.plotly_chart(fig_r, use_container_width=True, help="Trendline of brand visibility separated by Country.")
    else:
        st.info("No data available for the selected AI Platform.")
            
    st.markdown("---")
    
    # --- HEATMAP MATRIX ---
    st.subheader("Strategic Heatmap: Geographies vs AI Platforms", help="Displays your brand's Index vs Industry Average. 100 = Average. Grey with '-' means the brand has no presence or the AI platform is not available in this market.")
    
    hm_pivot = hm_df.pivot(index='country', columns='AI platform', values='index_vs_avg')
    hm_totals_pivot = hm_df.pivot(index='country', columns='AI platform', values='total')
    
    # Strict Ordering based on rules
    y_order = ["USA", "Brazil", "India", "China", "Indonesia"]
    x_order = ["Gemini", "Chat GPT", "Amazon Rufus", "Qwen", "AI Lazzie"]
    
    hm_pivot = hm_pivot.reindex(index=y_order, columns=x_order)
    hm_totals_pivot = hm_totals_pivot.reindex(index=y_order, columns=x_order)
    
    # Grey out invalid/zero data combinations
    hm_pivot_masked = hm_pivot.where((hm_totals_pivot.notna()) & (hm_pivot > 0), np.nan)
    
    text_array = []
    for r in hm_pivot_masked.values:
        row = []
        for v in r:
            if pd.isna(v) or v == 0:
                row.append("-")
            else:
                row.append(f"{v:.0f}")
        text_array.append(row)
    
    fig_hm = px.imshow(hm_pivot_masked, 
                       aspect="auto",
                       color_continuous_scale="RdYlGn",
                       color_continuous_midpoint=100, 
                       labels=dict(x="AI Platform", y="Geography", color="Index"))
    
    fig_hm.update_traces(text=text_array, texttemplate="%{text}")
    fig_hm.update_layout(
        xaxis_title="", 
        yaxis_title="",
        yaxis=dict(autorange="reversed"), 
        plot_bgcolor="#e2e8f0" 
    )
    st.plotly_chart(fig_hm, use_container_width=True)

# === TAB 2: SHARE OF VOICE (COMPETITIVE TRENDS) ===
elif selected_tab == "📊 Share of Voice Trends":
    st.subheader("Competitive Share of Voice Analysis", help="Compare your brand directly against the top 10 competitors in this category.")
    st.markdown("#### 1. SoV Evolution (Top 10 Brands)")
    
    daily_counts = scope_df.groupby(['date', 'mentioned_brands']).size().reset_index(name='count')
    
    if not daily_counts.empty:
        daily_totals = daily_counts.groupby('date')['count'].transform('sum')
        daily_counts['sov_pct'] = (daily_counts['count'] / daily_totals) * 100
        
        top_10 = scope_df['mentioned_brands'].value_counts().head(10).index.tolist()
        if target_brand not in top_10: top_10.append(target_brand) 
        
        filtered_daily = daily_counts[daily_counts['mentioned_brands'].isin(top_10)]
        
        fig_time_comp = px.line(filtered_daily, x='date', y='sov_pct', color='mentioned_brands',
                           labels={'sov_pct': 'Share of Voice (%)'},
                           markers=True)
        
        fig_time_comp.update_traces(opacity=0.3)
        fig_time_comp.update_traces(selector={'name':target_brand}, opacity=1, line={'width': 4})
        st.plotly_chart(fig_time_comp, use_container_width=True, help="Your selected brand is highlighted with a thicker, solid line.")
    else:
        st.info("No timeline data available.")
    
    st.markdown("#### 2. Platform Dominance (Top Brands)")
    plat_counts = scope_df.groupby(['AI platform', 'mentioned_brands']).size().reset_index(name='count')
    
    if not plat_counts.empty:
        if 'top_10' not in locals():
            top_10 = scope_df['mentioned_brands'].value_counts().head(10).index.tolist()
            
        plat_filtered = plat_counts[plat_counts['mentioned_brands'].isin(top_10)]
        
        fig_plat = px.bar(plat_filtered, x='AI platform', y='count', color='mentioned_brands',
                          barmode='stack')
        st.plotly_chart(fig_plat, use_container_width=True, help="Total aggregated mentions per platform broken down by top competitors.")
    else:
        st.info("No platform data available.")

# === TAB 3: BRAND PERCEPTION (NLP) ===
elif selected_tab == "💬 Brand Perception":
    st.subheader(f"How LLMs Describe '{target_brand}'", help="Semantic analysis of the exact phrasing AI assistants use when recommending this brand.")
    
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
            st.markdown("#### Top Descriptors")
            fig_bar = px.bar(wc_df, x='Frequency', y='Keyword', orientation='h',
                             color='Frequency', color_continuous_scale='Blues')
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True, help="The raw counts of the most frequently used adjectives alongside your brand.")
            
        with c2:
            st.markdown("#### Thematic Analysis")
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
            fig_radar = px.line_polar(theme_df, r='Count', theta='Theme', line_close=True)
            fig_radar.update_traces(fill='toself', line_color='#6366f1')
            st.plotly_chart(fig_radar, use_container_width=True, help="Maps the raw descriptors into strategic positioning buckets. Ensure the AI is not categorizing your premium brand as 'budget'.")
    else:
        st.warning("Not enough data to generate semantic analysis for this brand.")

# === TAB 4: SOURCE INTELLIGENCE ===
elif selected_tab == "🔗 Source Intelligence":
    st.subheader("Where is the LLM getting this info?", help="Traces the AI recommendations back to their origin authoritative sources across the web.")
    st.info("Based on citation patterns and known training data correlations.")
    
    brand_source_df = scope_df[scope_df['mentioned_brands'] == target_brand]
    
    if not brand_source_df.empty:
        source_counts = brand_source_df['source_citation'].value_counts().reset_index()
        source_counts.columns = ['Source', 'Mentions']
        
        c1, c2 = st.columns([2, 1])
        
        with c1:
            fig_tree = px.treemap(source_counts, path=['Source'], values='Mentions',
                                  color='Mentions', color_continuous_scale='RdBu')
            st.plotly_chart(fig_tree, use_container_width=True, help="Size of the box indicates the volume of brand mentions stemming from that specific source.")
            
        with c2:
            st.markdown("#### Actionable Targets")
            cat_sources = scope_df['source_citation'].value_counts(normalize=True)
            brand_sources = brand_source_df['source_citation'].value_counts(normalize=True)
            
            # Find where category average is higher than brand average
            gap = (cat_sources - brand_sources).dropna().sort_values(ascending=False).head(3)
            
            st.markdown("<p style='font-size: 14px; color: #64748b;'>Below are the sources your competitors are leveraging more effectively than you:</p>", unsafe_allow_html=True)
            if not gap.empty:
                for source, diff in gap.items():
                    st.warning(f"📉 **{source}**: Under-represented by {(diff*100):.1f}% vs category avg.")
            else:
                st.success("Your source distribution matches or exceeds the category average!")
    else:
        st.warning("No source data available for this brand.")
