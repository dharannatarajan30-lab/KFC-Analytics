import json
import pandas as pd
import plotly.express as px
import streamlit as st

# Configure the Streamlit page layout
st.set_page_config(
    page_title="KFC Swiggy Menu Dashboard",
    page_icon="🍗",
    layout="wide"
)

# Custom CSS to style metrics, backgrounds, headers, and eliminate empty top spaces
st.markdown("""
<style>
    /* 1. COLLAPSE EMPTY TOP SPACE & PADDING */
    /* Completely hide the default empty Streamlit header bar */
    header.stAppHeader, div[data-testid="stHeader"] {
        display: none !important;
        height: 0px !important;
        background-color: transparent !important;
    }

    /* Pull the main canvas up by overriding default block-container top padding */
    section.stMain .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
    }

    /* Pull the sidebar content up to the very top */
    div[data-testid="stSidebarUserContent"] {
        padding-top: 1rem !important;
    }

    /* 2. GENERAL APP THEME */
    /* Overall page background - clean warm white */
    .stApp {
        background-color: #FBFBFA !important;
    }

    /* Red and white diagonal stripe ribbon styled after the iconic KFC bucket design */
    .kfc-ribbon {
        background: repeating-linear-gradient(
            -45deg,
            #E4002B,
            #E4002B 15px,
            #FFFFFF 15px,
            #FFFFFF 30px
        );
        height: 14px;
        width: 100%;
        border-radius: 12px 12px 0 0;
        margin-bottom: 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    /* Styles the metric card box with a KFC red left accent border */
    div[data-testid="metric-container"], 
    div[data-testid="stMetric"], 
    .stMetric {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-left: 5px solid #E4002B !important; /* KFC Red accent stripe */
        padding: 20px 25px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease !important;
    }
    
    /* Interactive hover state to lift the cards and emit a subtle red glow */
    div[data-testid="metric-container"]:hover, 
    div[data-testid="stMetric"]:hover, 
    .stMetric:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 10px 25px rgba(228, 0, 43, 0.08) !important;
        border-color: #CBD5E1 !important;
        border-left: 5px solid #E4002B !important;
    }
    
    /* Styles the metric labels */
    div[data-testid="stMetricLabel"] p, 
    div[data-testid="metric-container"] label {
        font-weight: 600 !important;
        color: #4A5568 !important;
    }
    
    /* Styles the metric values */
    div[data-testid="stMetricValue"] > div, 
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        font-weight: 700 !important;
        color: #1A202C !important;
    }

    /* Custom sidebar elements for a tighter layout */
    section[data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 1px solid #E2E8F0 !important;
    }

    .sidebar-header {
        font-family: sans-serif;
        font-size: 0.95rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 6px;
    }

    .sidebar-divider {
        margin: 18px 0;
        border: 0;
        height: 1px;
        background: #E2E8F0;
    }

    /* Reduce default padding between sidebar text labels and native inputs */
    div[data-testid="stSidebar"] .stMultiSelect, 
    div[data-testid="stSidebar"] .stSlider {
        margin-top: -6px;
    }
</style>
""", unsafe_allow_html=True)

# Cache the data loader to prevent parsing JSON on every user interaction
@st.cache_data
def load_and_clean_data(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        raw_json = json.load(file)

    cards = raw_json.get("data", {}).get("cards", [])

    # Extract Restaurant Metadata
    restaurant_info = {}
    for card_wrapper in cards:
        card = card_wrapper.get("card", {}).get("card", {})
        if card.get("@type") == "type.googleapis.com/swiggy.gandalf.widgets.v2.Restaurant" or card.get("@type") == "type.googleapis.com/swiggy.presentation.food.v2.Restaurant":
            info = card.get("info", {})
            address = next(
                (label.get("message") for label in info.get("labels", []) if label.get("title") == "Address"), 
                "Not Available"
            )
            restaurant_info = {
                "id": info.get("id"),
                "name": info.get("name"),
                "city": info.get("city"),
                "locality": info.get("locality"),
                "area_name": info.get("areaName"),
                "cost_for_two": info.get("costForTwoMessage"),
                "avg_rating": info.get("avgRating", 0.0),
                "total_ratings": info.get("totalRatingsString"),
                "phone": info.get("phone"),
                "address": address
            }
            break

    # Flatten Menu Categories and Items
    menu_items = []
    for card_wrapper in cards:
        grouped_card = card_wrapper.get("groupedCard", {})
        if grouped_card:
            regular_cards = grouped_card.get("cardGroupMap", {}).get("REGULAR", {}).get("cards", [])
            for reg_card_wrapper in regular_cards:
                reg_card = reg_card_wrapper.get("card", {}).get("card", {})
                
                if reg_card.get("@type") == "type.googleapis.com/swiggy.presentation.food.v2.ItemCategory":
                    category_title = reg_card.get("title")
                    item_cards = reg_card.get("itemCards", [])
                    
                    for item_card_wrapper in item_cards:
                        dish = item_card_wrapper.get("card", {}).get("info", {})
                        
                        # Convert Swiggy price (paise) to Rupees
                        raw_price = dish.get("price") or dish.get("defaultPrice") or 0
                        price_rupees = raw_price / 100.0 if raw_price else 0.0
                        
                        raw_final_price = dish.get("finalPrice")
                        final_price_rupees = raw_final_price / 100.0 if raw_final_price else price_rupees
                        
                        rating_obj = dish.get("ratings", {}).get("aggregatedRating", {})
                        rating = rating_obj.get("rating")
                        rating_count = rating_obj.get("ratingCount")
                        
                        # Determine dietary classification (Separating Beverage)
                        if category_title == "BEVERAGE":
                            veg_classifier = "BEVERAGE"
                        else:
                            veg_classifier = dish.get("itemAttribute", {}).get("vegClassifier", "NONVEG")
                            if dish.get("isVeg") == 1:
                                veg_classifier = "VEG"
                            
                        is_bestseller = dish.get("isBestseller") or dish.get("ribbon", {}).get("text") == "Bestseller"
                        
                        image_id = dish.get("imageId")
                        image_url = (
                            f"https://media-assets.swiggy.com/swiggy/image/upload/fl_lossy,f_auto,q_auto,w_300,h_300/{image_id}"
                            if image_id else None
                        )
                        
                        menu_items.append({
                            "item_id": dish.get("id"),
                            "name": dish.get("name"),
                            "category": category_title,
                            "description": dish.get("description", ""),
                            "price": price_rupees,
                            "final_price": final_price_rupees,
                            "veg_or_nonveg": veg_classifier,
                            "in_stock": dish.get("inStock") == 1,
                            "rating": float(rating) if rating else None,
                            "rating_count": rating_count,
                            "is_bestseller": bool(is_bestseller),
                            "image_url": image_url
                        })

    df_menu = pd.DataFrame(menu_items)
    return restaurant_info, df_menu

# Load Data
try:
    restaurant, df_menu = load_and_clean_data("data.json")
except FileNotFoundError:
    st.error("Please place 'data.json' in the same folder as this script.")
    st.stop()


# --- SIDEBAR: RESTAURANT PROFILE (HTML Styled Brand Card) ---
st.sidebar.markdown(f"""
<div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-top: 5px solid #E4002B; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); margin-top: 5px; margin-bottom: 20px;">
    <h3 style="margin: 0 0 12px 0; color: #0F172A; font-size: 1.15rem; font-weight: 800; font-family: sans-serif; display: flex; align-items: center; gap: 8px;">
        🍗 {restaurant.get('name', 'KFC')} Analytics
    </h3>
    <div style="display: flex; flex-direction: column; gap: 10px; font-family: sans-serif; font-size: 0.88rem; color: #334155; line-height: 1.4;">
        <div>📍 <strong>Locality:</strong> {restaurant.get('locality')}, {restaurant.get('area_name')}</div>
        <div>⭐ <strong>Average Rating:</strong> {restaurant.get('avg_rating')} ({restaurant.get('total_ratings')})</div>
        <div>💰 <strong>Cost:</strong> {restaurant.get('cost_for_two')}</div>
        <div>📞 <strong>Phone:</strong> {restaurant.get('phone')}</div>
        <div style="border-top: 1px dashed #E2E8F0; margin-top: 6px; padding-top: 8px; font-size: 0.82rem; color: #64748B;">
            🏠 <strong>Address:</strong><br>{restaurant.get('address')}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# --- SIDEBAR: FILTERS SECTION ---
st.sidebar.markdown('<div class="sidebar-header" style="font-size: 1.05rem; color: #E4002B; margin-top: 5px; letter-spacing: 0.03em;">⚙️ FILTER DIVISIONS</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sidebar-divider" style="margin-top: 8px; margin-bottom: 15px;"></div>', unsafe_allow_html=True)

# Division 1: Dietary Preference
st.sidebar.markdown('<div class="sidebar-header">🥦 1. Dietary Preference</div>', unsafe_allow_html=True)
dietary_pref = st.sidebar.multiselect(
    "Select Dietary/Beverage Class:",
    options=["VEG", "NONVEG", "BEVERAGE"],
    default=[],
    label_visibility="collapsed" # Hide native label to keep formatting tight and custom
)
st.sidebar.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

# "Default to All" Logic - Step 1: 
active_diet = dietary_pref if dietary_pref else ["VEG", "NONVEG", "BEVERAGE"]

# Division 2: Categories (Dynamic based on Selection)
st.sidebar.markdown('<div class="sidebar-header">📂 2. Menu Categories</div>', unsafe_allow_html=True)
df_diet_filtered = df_menu[df_menu["veg_or_nonveg"].isin(active_diet)]
all_categories = sorted(df_diet_filtered["category"].unique())

selected_categories = st.sidebar.multiselect(
    "Select Categories:",
    options=all_categories,
    default=[],
    label_visibility="collapsed" # Hide native label
)
st.sidebar.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

# "Default to All" Logic - Step 2:
active_categories = selected_categories if selected_categories else all_categories

# Division 3: Budget/Price Range
st.sidebar.markdown('<div class="sidebar-header">💰 3. Budget Range</div>', unsafe_allow_html=True)
min_price = float(df_menu["final_price"].min())
max_price = float(df_menu["final_price"].max())
price_range = st.sidebar.slider(
    "Set Price Range (₹):",
    min_value=min_price,
    max_value=max_price,
    value=(min_price, max_price),
    label_visibility="collapsed" # Hide native label
)

# Apply filters to dataframe using the logically active selections
df_filtered = df_menu[
    (df_menu["veg_or_nonveg"].isin(active_diet)) &
    (df_menu["category"].isin(active_categories)) &
    (df_menu["final_price"] >= price_range[0]) &
    (df_menu["final_price"] <= price_range[1])
]

# --- MAIN DASHBOARD INTERFACE (KFC Branded Header) ---
st.markdown('<div class="kfc-ribbon"></div>', unsafe_allow_html=True)
st.markdown(f"""
<div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-top: none; padding: 22px 25px; border-radius: 0 0 12px 12px; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);">
    <h1 style="color: #0F172A; font-size: 2.35rem; font-weight: 800; margin: 0; letter-spacing: -0.025em; font-family: sans-serif;">
        🍗 {restaurant.get('name')} Cunningham Road - Menu Dashboard
    </h1>
    <p style="color: #64748B; font-size: 1.05rem; margin: 6px 0 0 0; font-family: sans-serif; font-weight: 500;">
        An interactive overview of menu pricing, items, and rating distributions.
    </p>
</div>
""", unsafe_allow_html=True)

# If for any reason the resulting list is physically empty (e.g. price slider set too tight)
if df_filtered.empty:
    st.markdown("---")
    st.warning("⚠️ **No items match your active filters.** Please widen your price range slider to display items.")
else:
    # KPI Cards Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Filtered Items", len(df_filtered))
    with col2:
        avg_price = df_filtered["final_price"].mean() if len(df_filtered) > 0 else 0
        st.metric("Average Item Price", f"₹{avg_price:.2f}")
    with col3:
        bestseller_count = df_filtered["is_bestseller"].sum()
        st.metric("Bestseller Items", bestseller_count)
    with col4:
        out_of_stock = len(df_filtered) - df_filtered["in_stock"].sum()
        st.metric("Out of Stock Items", out_of_stock)

    st.markdown("<br>", unsafe_allow_html=True)

    # Visualizations Row
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown('<div style="color: #0F172A; font-size: 1.25rem; font-weight: 700; border-bottom: 3px solid #E4002B; padding-bottom: 8px; width: fit-content; margin-bottom: 20px; font-family: sans-serif; text-transform: uppercase; letter-spacing: -0.01em;">Dietary Preference Distribution</div>', unsafe_allow_html=True)
        fig_pie = px.pie(
            df_filtered, 
            names='veg_or_nonveg', 
            color='veg_or_nonveg',
            color_discrete_map={'VEG': '#2ca02c', 'NONVEG': '#E4002B', 'BEVERAGE': '#3182ce'},
            hole=0.4
        )
        fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_chart2:
        st.markdown('<div style="color: #0F172A; font-size: 1.25rem; font-weight: 700; border-bottom: 3px solid #E4002B; padding-bottom: 8px; width: fit-content; margin-bottom: 20px; font-family: sans-serif; text-transform: uppercase; letter-spacing: -0.01em;">Average Price by Category</div>', unsafe_allow_html=True)
        avg_price_cat = df_filtered.groupby("category")["final_price"].mean().reset_index()
        avg_price_cat = avg_price_cat.sort_values(by="final_price", ascending=False)
        fig_bar = px.bar(
            avg_price_cat, 
            x="final_price", 
            y="category", 
            orientation="h",
            labels={"final_price": "Avg Price (₹)", "category": "Category"},
            color="final_price",
            color_continuous_scale=["#FFC5C5", "#E4002B"] # Monochromatic red palette for KFC branding
        )
        fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'}, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # Interactive Item List / Data Explorer
    st.markdown('<div style="color: #0F172A; font-size: 1.35rem; font-weight: 700; border-bottom: 3px solid #E4002B; padding-bottom: 8px; width: fit-content; margin-bottom: 20px; font-family: sans-serif; text-transform: uppercase; letter-spacing: -0.01em;">🔍 Menu Item Explorer</div>', unsafe_allow_html=True)
    search_query = st.text_input("Search items by name", "")

    if search_query:
        df_displayed = df_filtered[df_filtered["name"].str.contains(search_query, case=False)]
    else:
        df_displayed = df_filtered

    # Table display formatting
    df_table = df_displayed[[
        "name", "category", "veg_or_nonveg", "final_price", "rating", "is_bestseller", "in_stock"
    ]].copy()

    df_table.columns = ["Name", "Category", "Diet", "Price (₹)", "Rating", "Bestseller?", "In Stock"]
    st.dataframe(df_table, use_container_width=True, hide_index=True)