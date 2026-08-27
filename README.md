# KFC Analytics
# 🍗 KFC Swiggy Menu Dashboard

An interactive **Streamlit** dashboard that transforms raw, deeply nested Swiggy API JSON data 
into a clean, filterable analytics view for a KFC restaurant menu.

## ✨ Features

- **Automated JSON Parsing** — Extracts restaurant metadata (name, location, rating, address, 
  cost-for-two) and flattens deeply nested menu category/item structures from Swiggy's raw API 
  response into a clean Pandas DataFrame.
- **Smart Price Conversion** — Converts Swiggy's paise-based pricing to readable ₹ (INR) values, 
  handling both base price and discounted final price.
- **Dietary Classification** — Auto-tags each item as VEG / NONVEG / BEVERAGE using Swiggy's 
  veg classifier and item attributes.
- **Dynamic Sidebar Filters**
  - Dietary preference (Veg / Non-Veg / Beverage)
  - Menu category (auto-updates based on dietary selection)
  - Price range slider
- **Live KPI Metrics** — Total filtered items, average price, bestseller count, out-of-stock count.
- **Visual Analytics** (Plotly)
  - Donut chart: dietary preference distribution
  - Horizontal bar chart: average price by category
- **Searchable Data Explorer** — Full item table with name, category, diet type, price, rating, 
  bestseller flag, and stock status, with live text search.
- **Custom KFC-Branded UI** — Red/white striped ribbon header, styled metric cards, and a 
  branded restaurant profile card, all via custom CSS injected into Streamlit.
- **Performance** — Uses `@st.cache_data` to parse the JSON only once per session.

## 🛠️ Tech Stack

- **Python**
- **Streamlit** — UI framework
- **Pandas** — Data wrangling
- **Plotly Express** — Interactive charts

## 📂 How It Works

1. Place a Swiggy restaurant menu API response as `data.json` in the project root.
2. The script parses restaurant info and menu items into structured DataFrames.
3. Use the sidebar to filter by diet, category, and price.
4. Explore KPIs, charts, and a searchable item table in real time.

## 🚀 Run Locally

\`\`\`bash
pip install streamlit pandas plotly
streamlit run app.py
\`\`\`

Make sure `data.json` (Swiggy menu API dump) is in the same folder as the script.
