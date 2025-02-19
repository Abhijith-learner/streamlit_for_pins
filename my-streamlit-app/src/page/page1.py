import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import os

# st.set_page_config(page_title="Heatmap Dashboard", layout="wide")  # Sets a full-width layout

# ---------- Load Data Functions ----------
@st.cache_data
def load_data(file_path):
    if os.path.exists(file_path):
        return pd.read_excel(file_path)
    st.error(f"File not found: {file_path}")
    return None

@st.cache_data
def load_city_data(city_data_path):
    if os.path.exists(city_data_path):
        return pd.read_csv(city_data_path, encoding="utf-8")
    st.error(f"City data file not found: {city_data_path}")
    return None

@st.cache_data
def load_map_data(map_data_path):
    if os.path.exists(map_data_path):
        world = gpd.read_file(map_data_path)
        return world[world.ADMIN == "India"]
    st.error(f"Map data file not found: {map_data_path}")
    return None

# ---------- Data Processing ----------
def calculate_availability(data, city_data, product_filters="All Products",platform_filters=None,category_filters=None):

    if data is None or city_data is None:
        return None
    
    df = data.copy()
    df['Stock Availability (Y/N)'].fillna('No', inplace=True)
    df['available'] = df['Stock Availability (Y/N)'].apply(lambda x: 1 if x == 'Yes' else 0)
    
    # Apply filters for multiple selections
    if product_filters and "All Products" not in product_filters:
        df = df[df['Product Description'].isin(product_filters)]
    if category_filters and "All Category" not in category_filters:
        df = df[df['Category'].isin(category_filters)]
    if platform_filters and "All Platform" not in platform_filters:
        df = df[df['Platform'].isin(platform_filters)]

    # Filter by date range if specified
    # if start_date and end_date:
    #     df['Date'] = pd.to_datetime(df['Date'], errors='coerce')  # Ensure 'Date' is in datetime format
    #     df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

    availability_df = df.groupby('City')['available'].mean().reset_index()
    availability_df['availability_percentage'] = (availability_df['available'] * 100).round(2)
    
    availability_df = availability_df.merge(city_data, left_on="City", right_on="city", how="left").drop(columns=["city"])
    
    return availability_df

# ---------- Visualization ----------
def generate_map(availability_df, product_filter):
    if availability_df is None or availability_df.empty:
        st.warning("No data available for the selected product.")
        return None
    
    fig = px.scatter_mapbox(
        availability_df,
        lat="lat", lon="lng",
        size="availability_percentage",
        color="availability_percentage",
        color_continuous_scale="Viridis",
        hover_name="City",
        mapbox_style="open-street-map",
        zoom=4, height=600
    )
    
    fig.update_layout(title=f"Product Availability in India ({product_filter})")
    return fig

def calculate_stock_out_percentage(data, product_filters=None, platform_filters=None, category_filters=None):
    if data is None:
        return None
    
    df = data.copy()
    df['Stock Availability (Y/N)'].fillna('No', inplace=True)
    
    # Apply filters for multiple selections
    if product_filters and "All Products" not in product_filters:
        df = df[df['Product Description'].isin(product_filters)]
    if category_filters and "All Category" not in category_filters:
        df = df[df['Category'].isin(category_filters)]
    if platform_filters and "All Platform" not in platform_filters:
        df = df[df['Platform'].isin(platform_filters)]

    # Calculate stock-out percentage
    total_count = len(df)
    stock_out_count = len(df[df['Stock Availability (Y/N)'] == 'No'])
    
    stock_out_percentage = (stock_out_count / total_count * 100) if total_count > 0 else 0
    
    return round(stock_out_percentage, 2)


# ---------- Main App ----------
def main():
    st.title("📊 Heatmap Visualization Dashboard")
    
    # File Paths
    file_path = "data/competition.xlsx"
    city_data_path = "maps/india_city.csv"
    map_data_path = "maps/ne_110m_admin_0_countries.shp"
    
    # Load Data
    data = load_data(file_path)
    city_data = load_city_data(city_data_path)
    map_data = load_map_data(map_data_path)
    
    if data is not None:
        col1, col2 , col3 = st.columns([1, 3, 1])
        
        with col1:
            st.subheader("Select Products")
            unique_products = sorted(data['Product Description'].dropna().unique().tolist())
            selected_products = st.multiselect("Choose Products", unique_products, default=unique_products[:1])  # Default: First item

            st.subheader("Select Categories")
            unique_categories = sorted(data['Category'].dropna().unique().tolist())
            selected_categories = st.multiselect("Choose Categories", unique_categories, default=unique_categories[:1])

        with col3:
            st.subheader("Select Platforms")
            unique_platforms = sorted(data['Platform'].dropna().unique().tolist())
            selected_platforms = st.multiselect("Choose Platforms", unique_platforms, default=unique_platforms[:1])

            # Display Stock-Out Percentage
            stock_out_percentage = calculate_stock_out_percentage(data, selected_products, selected_platforms, selected_categories)
            st.metric(label="Stock-Out Percentage", value=f"{stock_out_percentage:.2f}%")

        with col2:
            st.subheader("Availability Percent by City")
            availability_df = calculate_availability(data, city_data, selected_products,selected_platforms,selected_categories)
            fig = generate_map(availability_df, selected_products,)
            if fig:
                st.plotly_chart(fig)

               

if __name__ == "__main__":
    main()
