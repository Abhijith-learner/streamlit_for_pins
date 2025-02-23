import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import os
from datetime import datetime


# st.set_page_config(page_title="Heatmap Dashboard", layout="wide")  # Sets a full-width layout

# Inject CSS to prevent the expansion of the multiselect box
st.markdown(
    """
    <style>
        /* Limit the selected items from expanding vertically */
        div[data-baseweb="tag"] {
            max-width: 1px !important;  /* Adjust based on preference */
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            display: inline-block !important;
        }
        
        /* Enable horizontal scrolling when too many items are selected */
        div[data-baseweb="select"] > div {
            display: flex !important;
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- Load Data Functions ----------
@st.cache_data
# Function to load data
def load_data(file_path):
    if os.path.exists(file_path):
        data= pd.read_excel(file_path,parse_dates=['Report Date'])
        return data
    else:
        st.error(f"Source data file not found: {file_path}")
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

def date_filter(fd,td,filtered_data):
    cop = filtered_data.copy()
    if "Report Date" in cop.columns:
        cop = cop[(cop['Report Date'] >= fd) & (cop['Report Date'] <= td)]
        return cop
    return filtered_data

def calculate_availability(data, city_data,from_date,to_date ,product_filters="All Products",platform_filters=None,category_filters=None):

    if data is None or city_data is None:
        return None
    
    df = data.copy()
    df['Stock Availability (Y/N)'].fillna('No', inplace=True)
    df['available'] = df['Stock Availability (Y/N)'].apply(lambda x: 1 if x == 'Yes' else 0)
    
    # Apply filters for multiple selections
    if product_filters and "All products" not in product_filters:
        df = df[df['Product Description'].isin(product_filters)]
    if category_filters and "All categories" not in category_filters:
        df = df[df['Category'].isin(category_filters)]
    if platform_filters and "All platforms" not in platform_filters:
        df = df[df['Platform'].isin(platform_filters)]


    df = date_filter(from_date,to_date,df)

    # st.write("in availability function",df)

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
    
    fig.update_layout(title=f"Product Availability in India.")
    return fig

def calculate_stock_out_percentage(data,selected_date_from,selected_date_to, product_filters=None, platform_filters=None, category_filters=None):
    if data is None:
        return None
    
    df = data.copy()
    df['Stock Availability (Y/N)'].fillna('No', inplace=True)
    
    # Apply filters for multiple selections
    if product_filters and "All products" not in product_filters:
        df = df[df['Product Description'].isin(product_filters)]
    if category_filters and "All categories" not in category_filters:
        df = df[df['Category'].isin(category_filters)]
    if platform_filters and "All platforms" not in platform_filters:
        df = df[df['Platform'].isin(platform_filters)]

    df = date_filter(selected_date_from,selected_date_to,df)
    # Calculate stock-out percentage
    total_count = len(df,)
    stock_out_count = len(df[df['Stock Availability (Y/N)'] == 'No'])
    
    stock_out_percentage = (stock_out_count / total_count * 100) if total_count > 0 else 0
    
    return round(stock_out_percentage, 2)

def average_sale_price(data,selected_date_from,selected_date_to, product_filters=None, platform_filters=None, category_filters=None):
    if data is None:
        return None
    
    df = data.copy()
    
    # Apply filters
    if product_filters and "All products" not in product_filters:
        df = df[df['Product Description'].isin(product_filters)]
    if category_filters and "All categories" not in category_filters:
        df = df[df['Category'].isin(category_filters)]
    if platform_filters and "All platforms" not in platform_filters:
        df = df[df['Platform'].isin(platform_filters)]

    # filter on DATE
    df = date_filter(selected_date_from,selected_date_to,df)
        
    
    # Calculate average selling price
    if 'Selling Price' in df.columns:
        avg_price = df['Selling Price'].mean()
        return round(avg_price, 2)
    
    return None

def average_discount(data, selected_date_from,selected_date_to,product_filters=None, platform_filters=None, category_filters=None):
    if data is None:
        return None
    
    df = data.copy()
    
    # Apply filters
    if product_filters and "All products" not in product_filters:
        df = df[df['Product Description'].isin(product_filters)]
    if category_filters and "All categories" not in category_filters:
        df = df[df['Category'].isin(category_filters)]
    if platform_filters and "All platforms" not in platform_filters:
        df = df[df['Platform'].isin(platform_filters)]

    # DATE filter 
    df = date_filter(selected_date_from,selected_date_to,df)
       
    
    # Ensure 'Discount' column exists
    if 'Discount' in df.columns:
        print('column found')
        df['Discount'] = df['Discount'].astype(str).str.replace("%", "", regex=True)  # Remove '%' symbol
        df['Discount'] = pd.to_numeric(df['Discount'], errors='coerce')  # Convert to numeric (NaN for blanks)
        
        avg_discount = df['Discount'].mean(skipna=True)  # Ignore NaN values
        return round(avg_discount, 2) if not pd.isna(avg_discount) else 0  # Return 0 if all values are NaN
    
    return 'NA'  # Return NA if the column doesn't exist


    
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
            # st.subheader("Select Products")
            unique_products = sorted(data['Product Description'].dropna().unique().tolist())
            # unique_products.insert(0,"All products")
            selected_products = st.multiselect("Choose Products", unique_products, default=unique_products[0])  # Default: First item

            unique_categories = sorted(data['Category'].dropna().unique().tolist())
            # unique_categories.insert(0,"All categories")
            selected_categories = st.multiselect("Choose Categories", unique_categories, default=unique_categories[0])

        with col3:

        
            # Calculate min and max dates from the data
            min_date = data['Report Date'].min().strftime('%d/%m/%Y')
            max_date = data['Report Date'].max().strftime('%d/%m/%Y')

            # st.subheader("Date") #FROMDATE
            selected_date_from = st.date_input("From Date", value=datetime.strptime(min_date, '%d/%m/%Y').date(), min_value=datetime.strptime(min_date, '%d/%m/%Y').date(), max_value=datetime.strptime(max_date, '%d/%m/%Y').date())
            selected_date_from = selected_date_from.strftime('%d/%m/%Y')
            # TODATE
            selected_date_to = st.date_input("To Date", value=datetime.strptime(max_date, '%d/%m/%Y').date(), min_value=datetime.strptime(min_date, '%d/%m/%Y').date(), max_value=datetime.strptime(max_date, '%d/%m/%Y').date())
            selected_date_to = selected_date_to.strftime('%d/%m/%Y')

            # st.subheader("Select Platforms")
            unique_platforms = sorted(data['Platform'].dropna().unique().tolist())
            # unique_platforms.insert(0,'All platforms')
            selected_platforms = st.multiselect("Choose Platforms", unique_platforms, default=unique_platforms[0])

            # Display Stock-Out Percentage
            stock_out_percentage = calculate_stock_out_percentage(data,selected_date_from,selected_date_to,selected_products, selected_platforms, selected_categories)
            st.metric(label="Stock-Out Percentage", value=f"{stock_out_percentage:.2f}%")


            # Display AVG sale price
            average_selling_price = average_sale_price(data,selected_date_from,selected_date_to,selected_products, selected_platforms, selected_categories)
            st.metric(label="Average selling price", value=f"{average_selling_price}")

            # Display AVG Discount
            average_discount_value = average_discount(data,selected_date_from,selected_date_to, selected_products, selected_platforms, selected_categories)
            st.metric(label="Average Discount", value=f"{average_discount_value:}%")


        with col2:
            st.subheader("Availability Percent by City")
            availability_df = calculate_availability(data,city_data,selected_date_from,selected_date_to,selected_products,selected_platforms,selected_categories)
            fig = generate_map(availability_df, selected_products,)
            if fig:
                st.plotly_chart(fig)

               
    # Footer
    st.markdown("**Powered by Purple Block**")
if __name__ == "__main__":
    main()
