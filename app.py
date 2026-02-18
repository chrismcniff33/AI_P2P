import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# --- 1. PAGE CONFIGURATION & STYLING ---
st.set_page_config(page_title="AI Brand Intelligence", page_icon="🧠", layout="wide")

# Custom CSS to tighten layout and give it a "Dashboard" feel
st.markdown("""
    <style>
        .block-container {padding-top: 1rem; padding-bottom: 0rem; padding-left: 2rem; padding-right: 2rem;}
        h1 {color: #4F46E5; font-size: 2.5rem;}
        h3 {color: #1F2937;}
        div[data-testid="stMetricValue"] {font-size: 1.8rem; color: #4F46E5;}
        .stTabs [data-baseweb="tab-list"] {gap: 10px;}
        .stTabs [data-baseweb="tab"] {height: 50px; white-space: pre-wrap; background-color: #F3F4F6; border-radius: 4px 4px 0px 0px; gap: 1px; padding-top: 10px; padding-bottom: 10px;}
        .stTabs [aria-selected="true"] {background-color: #4F46E5; color: white;}
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

    # Show input for password.
    st.text_input(
        "Please enter the password to access the dashboard", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

if not check_password():
    st.stop()  # Do not continue if check_password is not True.

# --- 3. DATA LOADING (UPDATED FOR ZIP) ---
@st.cache_data
def load_data():
    # Pandas automatically handles ZIP compression!
    # It will open the zip and read the first CSV file inside.
    df = pd.read_csv("ultimate_ai_dataset_contextual.zip")
    df['date'] = pd.to_datetime(df['date'])
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("❌ ZIP file not found. Please ensure 'ultimate_ai_dataset_contextual.zip' is in the GitHub repository.")
    st.stop()
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

# Helper: Extract brands between **bold** markers
def extract_brands(text):
    return re.findall(r'\*\*(.*?)\*\*', str(text))

# --- 4. SIDEBAR CONTROLS ---
with st.sidebar:
    st.title("🎛️ Control Panel")
    
    # Global Category Filter (Applies to everything)
    categories = sorted(df['category'].unique())
    selected_category = st.selectbox("Select Category", categories)
    
    st.markdown("---")
    st.caption(f"Analyzing {len(df):,} total AI responses.")
    st.caption("Data range: Jan 5 - Feb 9, 2026")

# Apply Global Filter
df_cat = df[df['category'] == selected_category]

# --- 5. TOP KPI ROW ---
# Calculate high-level metrics
total_prompts = len(df_cat)
all_brands = []
for r in df_cat['response']:
    all_brands.extend(extract_brands(r))
unique_brands = len(set(all_brands))
# Calculate top brand safely
top_brand_global = pd.Series(all_brands).mode()[0] if all_brands else "N/A"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Interactions", f"{total_prompts:,}")
col2.metric("Unique Brands Found", unique_brands)
col3.metric("Top Brand (Global)", top_brand_global)
col4.metric("Active Countries", len(df_cat['country'].unique()))

st.markdown("---")

# --- 6. TABBED INTERFACE ---
tab1, tab2, tab3 = st.tabs(["📈 Market Overview", "⚔️ Head-to-Head Compare", "🔍 Raw Data"])

# === TAB 1: OVERVIEW ===
with tab1:
    # Row 1: Timeline & Share of Voice
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("Simulated Search Volume")
        daily = df_cat.groupby('date').size().reset_index(name='count')
        fig_line = px.area(daily, x='date', y='count', markers=True, 
                           color_discrete_sequence=['#4F46E5'])
        fig_line.update_layout(xaxis_title="", yaxis_title="Prompts", height=350)
        st.plotly_chart(fig_line, use_container_width=True)
        
    with c2:
        st.subheader("Platform Activity")
        plat_counts = df_cat['AI platform'].value_counts()
        fig_donut = px.pie(values=plat_counts.values, names=plat_counts.index, hole=0.5,
                           color_discrete_sequence=px.colors.qualitative.Prism)
        fig_donut.update_layout(showlegend=False, height=350)
        st.plotly_chart(fig_donut, use_container_width=True)

    # Row 2: Brand Leaderboard
    st.subheader(f"🏆 Top Recommended Brands: {selected_category}")
    
    # Get top brands for the selected category
    cat_brands = []
    for r in df_cat['response']:
        cat_brands.extend(extract_brands(r))
    
    if cat_brands:
        brand_counts = pd.Series(cat_brands).value_counts().head(15).reset_index()
        brand_counts.columns = ['Brand', 'Mentions']
        
        fig_bar = px.bar(brand_counts, x='Mentions', y='Brand', orientation='h',
                         color='Mentions', color_continuous_scale='Viridis', text_auto=True)
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, height=500)
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No brands detected in responses.")

# === TAB 2: HEAD-TO-HEAD COMPARISON ===
with tab2:
    st.markdown("### ⚔️ Country & Platform Standoff")
    st.write("Compare how recommendations differ between two regions or platforms.")
    
    # Comparison Filters
    col_a, col_mid, col_b = st.columns([1, 0.1, 1])
    
    with col_a:
        st.info("Side A Configuration")
        country_a = st.selectbox("Country A", sorted(df['country'].unique()), index=0, key="ca")
        platform_a = st.selectbox("Platform A", ["All"] + sorted(df['AI platform'].unique()), index=0, key="pa")
        
    with col_b:
        st.success("Side B Configuration")
        country_b = st.selectbox("Country B", sorted(df['country'].unique()), index=1, key="cb")
        platform_b = st.selectbox("Platform B", ["All"] + sorted(df['AI platform'].unique()), index=0, key="pb")

    # Filter Data for Sides
    df_a = df_cat[df_cat['country'] == country_a]
    if platform_a != "All": df_a = df_a[df_a['AI platform'] == platform_a]
    
    df_b = df_cat[df_cat['country'] == country_b]
    if platform_b != "All": df_b = df_b[df_b['AI platform'] == platform_b]

    # Process Brands for Sides
    def get_top_brands_df(dataframe):
        b_list = []
        for r in dataframe['response']:
            b_list.extend(extract_brands(r))
        if not b_list: return pd.DataFrame(columns=['Brand', 'Mentions'])
        return pd.Series(b_list).value_counts().head(10).reset_index().rename(columns={'index':'Brand', 0:'Mentions'})

    brands_a = get_top_brands_df(df_a)
    brands_b = get_top_brands_df(df_b)

    # Display Visual Comparison
    st.divider()
    
    viz_col_a, viz_col_b = st.columns(2)
    
    with viz_col_a:
        st.subheader(f"Top in {country_a}")
        if not brands_a.empty:
            fig_a = px.bar(brands_a, x='Mentions', y='Brand', orientation='h', title=None)
            fig_a.update_traces(marker_color='#3b82f6') # Blue
            fig_a.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_a, use_container_width=True)
        else:
            st.warning("No data found for selection A")

    with viz_col_b:
        st.subheader(f"Top in {country_b}")
        if not brands_b.empty:
            fig_b = px.bar(brands_b, x='Mentions', y='Brand', orientation='h', title=None)
            fig_b.update_traces(marker_color='#10b981') # Green
            fig_b.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_b, use_container_width=True)
        else:
            st.warning("No data found for selection B")

# === TAB 3: RAW DATA ===
with tab3:
    st.markdown("### 📂 Data Explorer")
    
    # Search Bar
    search_term = st.text_input("Search prompts or responses (e.g., 'dandruff', 'Sony', 'cheap')")
    
    view_df = df_cat
    if search_term:
        view_df = df_cat[df_cat['prompt'].str.contains(search_term, case=False) | 
                         df_cat['response'].str.contains(search_term, case=False)]
    
    st.dataframe(
        view_df[['date', 'country', 'AI platform', 'criteria', 'prompt', 'response']], 
        use_container_width=True,
        height=600
    )
