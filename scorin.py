import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Function to load data
def load_data(file_path):
    if os.path.exists(file_path):
        return pd.read_excel(file_path)
    else:
        st.error(f"Source data file not found: {file_path}")
        return None

# Function to create the top container with filters
def create_top_container(data):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.subheader("Select Category")
        categories = data['Category'].unique().tolist()
        selected_categories = st.multiselect("Categories", categories)
        
    with col2:
        st.subheader("Select Date")
        selected_date = st.date_input("Date", datetime.date(2024, 12, 17))
        
    with col3:
        st.subheader("Select Platform")
        platforms = data['Platform'].unique().tolist()
        selected_platforms = st.multiselect("Platforms", platforms)
        
    with col4:
        st.subheader("Select City")
        cities = data['City'].unique().tolist()
        selected_cities = st.multiselect("Cities", cities)
        
    return selected_categories, selected_date, selected_platforms, selected_cities

# Function to create the bottom container with plots
def bottom_container(filtered_data):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Select Product")
        if filtered_data is not None:
            products = filtered_data['Product Description'].unique().tolist()
            selected_products = st.multiselect("Products", products)
        else:
            selected_products = []
    
        
    with col2:
        st.subheader("Availability % and Avg Discount % by Brand")
        if filtered_data is not None and 'Discount' in filtered_data.columns and 'Stock Availability (Y/N)' in filtered_data.columns:
            # Ensure Discount column is in percentage format
            filtered_data['Discount'] = pd.to_numeric(filtered_data['Discount'].str.replace('%', ''), errors='coerce')
            
            # Convert Availability to binary format
            filtered_data['Availability Binary'] = filtered_data['Stock Availability (Y/N)'].apply(lambda x: 1 if x == 'Yes' else 0)
            
            # Calculate availability percentage for each brand
            availability_percentage = filtered_data.groupby('Brand')['Availability Binary'].mean().reset_index()
            availability_percentage.columns = ['Brand', 'Availability Proportion']
            
            # Convert proportion to percentage
            availability_percentage['Availability Percentage'] = availability_percentage['Availability Proportion'] * 100
            
            # Merge availability percentage with the original data
            filtered_data = filtered_data.merge(availability_percentage, on='Brand', how='left')
            
            # Grouped bar chart for discount and availability by brand
            fig = px.bar(
                filtered_data,
                x='Brand',
                y=['Discount', 'Availability Percentage'],
                barmode='group',
                title='Availability % and Avg Discount % by Brand'
            )
            
            # Update y-axis range to 0-100
            fig.update_yaxes(range=[0, 100], autorange=False)
            
            st.plotly_chart(fig)
        else:
            st.write("No discount or availability data available.")

    return selected_products

# Main function to run the app
def run():
    global data
    data = load_data("data/competition.xlsx")
    
    if data is not None:
        selected_categories, selected_date, selected_platforms, selected_cities = create_top_container(data)
        
        # Filter data based on selected options
        filtered_data = data.copy()
        if selected_categories:
            filtered_data = filtered_data[filtered_data['Category'].isin(selected_categories)]
        if selected_date:
            filtered_data = filtered_data[filtered_data['Report Date'] == selected_date]
        if selected_platforms:
            filtered_data = filtered_data[filtered_data['Platform'].isin(selected_platforms)]
        if selected_cities:
            filtered_data = filtered_data[filtered_data['City'].isin(selected_cities)]
        
        selected_products = bottom_container(filtered_data)
        
        # Further filter data based on selected products
        if selected_products:
            filtered_data = filtered_data[filtered_data['Product Description'].isin(selected_products)]
        
        # Display filtered data
        st.write(filtered_data)

    # Footer
    st.markdown("**Powered by Purple Block**")

if __name__ == "__main__":
    run()