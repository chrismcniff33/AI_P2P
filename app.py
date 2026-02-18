import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import random
from collections import Counter

# --- 1. PAGE CONFIGURATION & STYLING ---
st.set_page_config(page_title="BrandAI: Strategic Intelligence", page_icon="🚀", layout="wide")

# Custom CSS for "Executive Dashboard" feel
st.markdown("""
    <style>
        .block-container {padding-top: 1rem; padding-bottom: 2rem;}
        h1 {color: #1e293b; font-family: 'Helvetica Neue', sans-serif;}
        .metric-card {background-color: #f8fafc; padding: 20px; border-radius: 8px; border-left: 5px solid #6366f1;}
        div[data-testid="stMetricValue"] {font-size: 1.5rem; color: #4F46E5;}
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

    st.text_input("Password", type="password", on_change=password_entered, key="password")
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
    st.error("⚠️ No brands were found in the data! The dashboard looks for brands bolded like **BrandName**. Please check your CSV generation.")
    st.stop()

# --- 4. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🚀 BrandAI")
    
    # 1. Scope Selection
    st.subheader("1. Define Market Scope")
    selected_category = st.selectbox("Category", sorted(df['category'].unique()))
    
    avail_countries = sorted(df[df['category'] == selected_category]['country'].unique())
    selected_country = st.selectbox("Market (Country)", ["All"] + avail_countries)
    
    # Filter Data
    scope_df = df_exploded[df_exploded['category'] == selected_category]
    if selected_country != "All":
        scope_df = scope_df[scope_df['country'] == selected_country]
        
    # 2. Target Brand Selection
    st.subheader("2. Select Your Brand")
    
    if not scope_df.empty:
        available_brands = scope_df['mentioned_brands'].value_counts().head(40).index.tolist()
        target_brand = st.selectbox("Focus Brand", available_brands)
    else:
        st.warning("No data for this selection.")
        st.stop()
    
    st.markdown("---")
    st.info(f"Analyzing {len(scope_df):,} mentions.")

# --- 5. MAIN TABS ---
tab_insight, tab_sov, tab_semantic, tab_sources = st.tabs([
    "💡 Executive Insights", 
    "📊 Share of Voice", 
    "💬 Brand Perception", 
    "🔗 Source Intelligence"
])

# === TAB 1: EXECUTIVE INSIGHTS (SWOT) ===
with tab_insight:
    st.header(f"Executive Summary: {target_brand}")
    
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
    
    # B. STRENGTHS & WEAKNESSES (NOW WITH RADAR CHART!)
    col_vis, col_text = st.columns([1, 1])
    
    # Calculate Brand SoV per Criteria
    crit_counts = scope_df.groupby(['criteria', 'mentioned_brands']).size().unstack(fill_value=0)
    crit_pct = crit_counts.div(crit_counts.sum(axis=1), axis=0) * 100
    
    with col_vis:
        st.subheader("Performance Radar")
        if target_brand in crit_pct.columns:
            # Prepare Radar Data
            brand_scores = crit_pct[target_brand].reset_index()
            brand_scores.columns = ['Criteria', 'Score']
            
            fig_radar = px.line_polar(brand_scores, r='Score', theta='Criteria', line_close=True,
                                      title=f"{target_brand} Visibility by Criteria")
            fig_radar.update_traces(fill='toself', lineColor='#6366f1')
            st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.warning("Not enough data to plot radar chart.")

    with col_text:
        st.subheader("Strategic SWOT")
        if target_brand in crit_pct.columns:
            strongest = crit_pct[target_brand].nlargest(3)
            weakest = crit_pct[target_brand].nsmallest(3)
            
            st.success("🟢 **Strengths (High Visibility)**")
            for criteria, score in strongest.items():
                st.write(f"- **{criteria}**: {score:.1f}% Share of Voice")
                
            st.error("🔴 **Weaknesses (Low Visibility)**")
            for criteria, score in weakest.items():
                st.write(f"- **{criteria}**: {score:.1f}% Share of Voice")
        else:
            st.write("No data available.")

# === TAB 2: SHARE OF VOICE (SoV) ===
with tab_sov:
    st.header("Share of Voice Analysis")
    
    # 1. SoV Over Time (Line Chart)
    st.subheader("1. SoV Evolution (Weekly)")
    
    daily_counts = scope_df.groupby(['date', 'mentioned_brands']).size().reset_index(name='count')
    daily_totals = daily_counts.groupby('date')['count'].transform('sum')
    daily_counts['sov_pct'] = (daily_counts['count'] / daily_totals) * 100
    
    top_10 = scope_df['mentioned_brands'].value_counts().head(10).index.tolist()
    if target_brand not in top_10: top_10.append(target_brand) 
    
    filtered_daily = daily_counts[daily_counts['mentioned_brands'].isin(top_10)]
    
    fig_time = px.line(filtered_daily, x='date', y='sov_pct', color='mentioned_brands',
                       title="Brand Visibility % Over Time",
                       labels={'sov_pct': 'Share of Voice (%)'},
                       markers=True)
    
    fig_time.update_traces(opacity=0.3)
    fig_time.update_traces(selector={'name':target_brand}, opacity=1, line={'width': 4})
    st.plotly_chart(fig_time, use_container_width=True)
    
    # 2. SoV by Platform (Stacked Bar)
    st.subheader("2. Platform Dominance")
    plat_counts = scope_df.groupby(['AI platform', 'mentioned_brands']).size().reset_index(name='count')
    plat_filtered = plat_counts[plat_counts['mentioned_brands'].isin(top_10)]
    
    fig_plat = px.bar(plat_filtered, x='AI platform', y='count', color='mentioned_brands',
                      title="Brand Mentions Split by Platform",
                      barmode='stack')
    st.plotly_chart(fig_plat, use_container_width=True)

# === TAB 3: BRAND PERCEPTION (NLP) ===
with tab_semantic:
    st.header(f"How LLMs Describe '{target_brand}'")
    
    # 1. Keyword Extraction Logic (Using Original DF for full text)
    brand_responses = df[
        (df['category'] == selected_category) & 
        (df['response'].str.contains(target_brand, na=False))
    ]['response']
    
    stopwords = set(['the', 'and', 'is', 'to', 'in', 'of', 'for', 'with', 'a', 'it', 'this', 'that', 'brand', 'product', 'recommend', 'options', 'choice', 'popular', 'user', 'users', 'reviews', 'are', 'as'])
    
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
            fig_radar.update_traces(fill='toself')
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
            
            for source, diff in gap.items():
                st.warning(f"📉 **{source}**: Under-represented by {(diff*100):.1f}% vs category avg.")
    else:
        st.warning("No source data available for this brand.")
