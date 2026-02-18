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
        h2 {color: #334155; font-size: 1.5rem; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;}
        .metric-card {background-color: #f8fafc; padding: 20px; border-radius: 8px; border-left: 5px solid #6366f1; box-shadow: 0 2px 4px rgba(0,0,0,0.05);}
        div[data-testid="stMetricValue"] {font-size: 1.5rem; color: #4F46E5;}
    </style>
""", unsafe_allow_html=True)

# --- 2. PASSWORD PROTECTION LOGIC ---
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["passwords"]["dashboard_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.text_input(
        "Please enter the password to access the dashboard", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
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

    # --- A. INJECT DUMMY SOURCES (On the Fly) ---
    # We map categories to realistic "LLM Sources" to simulate where the AI found the info
    source_db = {
        "Shampoo": ["Allure Magazine", "Reddit r/HaircareScience", "Sephora Reviews", "Vogue Beauty", "Byrdie", "YouTube (Brad Mondo)", "MakeupAlley"],
        "TVs": ["RTings.com", "The Verge", "Reddit r/4kTV", "CNET", "TechRadar", "YouTube (Linus Tech Tips)", "Consumer Reports"],
        "Dog food": ["DogFoodAdvisor", "Reddit r/dogs", "Chewy.com Reviews", "AKC.org", "Veterinary Partner", "PetMD"],
        "Dietary supplements": ["Examine.com", "Healthline", "NIH.gov", "Amazon Reviews", "Labdoor", "Reddit r/Supplements"]
    }

    def assign_source(row):
        cat_sources = source_db.get(row['category'], ["General Web Search"])
        return random.choice(cat_sources)

    # Apply source injection
    df['source_citation'] = df.apply(assign_source, axis=1)
    
    # --- B. EXTRACT BRANDS ---
    def extract_brands_list(text):
        # Extract text between double asterisks (e.g. **Samsung**)
        return re.findall(r'\*\*(.*?)\*\*', str(text))
    
    df['mentioned_brands'] = df['response'].apply(extract_brands_list)
    
    # Explode dataset so each brand mention has its own row (Critical for Share of Voice)
    df_exploded = df.explode('mentioned_brands')
    
    return df, df_exploded

# Load Data
df, df_exploded = load_and_enrich_data()

# --- 4. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🚀 BrandAI")
    
    # 1. Scope Selection
    st.subheader("1. Define Market Scope")
    selected_category = st.selectbox("Category", sorted(df['category'].unique()))
    
    # Filter countries available for this category
    avail_countries = sorted(df[df['category'] == selected_category]['country'].unique())
    selected_country = st.selectbox("Market (Country)", ["All"] + avail_countries)
    
    # Filter Data based on Scope
    # 'scope_df' is the exploded version (one row per brand mention)
    scope_df = df_exploded[df_exploded['category'] == selected_category]
    if selected_country != "All":
        scope_df = scope_df[scope_df['country'] == selected_country]
        
    # 2. Target Brand Selection (For Insights Panel)
    st.subheader("2. Select Your Brand")
    
    # Get top 30 brands in this specific scope for the dropdown
    if not scope_df.empty:
        available_brands = scope_df['mentioned_brands'].value_counts().head(30).index.tolist()
        target_brand = st.selectbox("Focus Brand", available_brands)
    else:
        st.warning("No data for this selection.")
        st.stop()
    
    st.markdown("---")
    st.info(f"Analyzing {len(scope_df):,} mentions in {selected_category}.")

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
    
    # Calculate SoV %
    sov = (brand_mentions / total_mentions) * 100 if total_mentions > 0 else 0
    
    # Calculate Rank
    rank_df = scope_df['mentioned_brands'].value_counts().reset_index()
    rank_df.columns = ['Brand', 'Count']
    try:
        rank = rank_df[rank_df['Brand'] == target_brand].index[0] + 1
    except:
        rank = "N/A"

    # Top Co-occurring Competitor (Rank #1 that isn't the target)
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
    
    # B. STRENGTHS & WEAKNESSES GRID
    col_str, col_weak = st.columns(2)
    
    # Calculate Brand SoV per Criteria
    # (How often does Target Brand appear for 'Budget' vs 'Premium'?)
    crit_counts = scope_df.groupby(['criteria', 'mentioned_brands']).size().unstack(fill_value=0)
    # Convert to % of total mentions for that criteria
    crit_pct = crit_counts.div(crit_counts.sum(axis=1), axis=0) * 100
    
    with col_str:
        st.subheader("🟢 Where You Win (Strengths)")
        if target_brand in crit_pct.columns:
            strongest = crit_pct[target_brand].nlargest(3)
            for criteria, score in strongest.items():
                st.success(f"**{criteria}**: {score:.1f}% Share of Voice")
        else:
            st.warning("No significant data for strengths.")

    with col_weak:
        st.subheader("🔴 Areas to Address (Weaknesses)")
        if target_brand in crit_pct.columns:
            weakest = crit_pct[target_brand].nsmallest(3)
            for criteria, score in weakest.items():
                st.error(f"**{criteria}**: Only {score:.1f}% Share of Voice")
        else:
            st.warning("No significant data for weaknesses.")

# === TAB 2: SHARE OF VOICE (SoV) ===
with tab_sov:
    st.header("Share of Voice Analysis")
    
    # 1. SoV Over Time (Line Chart)
    st.subheader("1. SoV Evolution (Weekly)")
    
    # Group by Date and Brand
    daily_counts = scope_df.groupby(['date', 'mentioned_brands']).size().reset_index(name='count')
    # Calculate total per day to get %
    daily_totals = daily_counts.groupby('date')['count'].transform('sum')
    daily_counts['sov_pct'] = (daily_counts['count'] / daily_totals) * 100
    
    # Filter to top 10 brands to prevent chart clutter
    top_10 = scope_df['mentioned_brands'].value_counts().head(10).index.tolist()
    if target_brand not in top_10: top_10.append(target_brand) 
    
    filtered_daily = daily_counts[daily_counts['mentioned_brands'].isin(top_10)]
    
    fig_time = px.line(filtered_daily, x='date', y='sov_pct', color='mentioned_brands',
                       title="Brand Visibility % Over Time",
                       labels={'sov_pct': 'Share of Voice (%)'},
                       markers=True)
    
    # Highlight target brand visually
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
    
    # 1. Keyword Extraction Logic
    # Get all responses mentioning the target brand from the ORIGINAL dataframe (not exploded)
    # We filter the raw DF to ensure we get the full text context
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
        
    # Count frequency
    if all_words:
        word_counts = Counter(all_words).most_common(20)
        wc_df = pd.DataFrame(word_counts, columns=['Keyword', 'Frequency'])
        
        c1, c2 = st.columns([1, 1])
        
        with c1:
            st.subheader("Top Descriptors")
            fig_bar = px.bar(wc_df, x='Frequency', y='Keyword', orientation='h',
                             title=f"Most Common Words Associated with {target_brand}",
                             color='Frequency', color_continuous_scale='Blues')
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with c2:
            st.subheader("Thematic Analysis")
            # Simple rule-based clustering
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
    
    # Filter data for target brand mentions
    brand_source_df = scope_df[scope_df['mentioned_brands'] == target_brand]
    
    if not brand_source_df.empty:
        # 1. Top Sources for Brand
        source_counts = brand_source_df['source_citation'].value_counts().reset_index()
        source_counts.columns = ['Source', 'Mentions']
        
        c1, c2 = st.columns([2, 1])
        
        with c1:
            fig_tree = px.treemap(source_counts, path=['Source'], values='Mentions',
                                  title=f"Top Sources Driving Visibility for {target_brand}",
                                  color='Mentions', color_continuous_scale='RdBu')
            st.plotly_chart(fig_tree, use_container_width=True)
            
        with c2:
            st.subheader("Actionable Targets")
            st.write("To increase visibility, target these under-indexed sources:")
            
            # Compare Global Category Sources vs Brand Sources
            cat_sources = scope_df['source_citation'].value_counts(normalize=True)
            brand_sources = brand_source_df['source_citation'].value_counts(normalize=True)
            
            # Find gap
            # We look for sources where the Category is high but the Brand is low
            gap = (cat_sources - brand_sources).dropna().sort_values(ascending=False).head(3)
            
            for source, diff in gap.items():
                st.warning(f"📉 **{source}**: You are under-represented by {(diff*100):.1f}% compared to category avg.")
    else:
        st.warning("No source data available for this brand.")
