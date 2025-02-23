import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# Function to load data
@st.cache_data
def load_data(file_path):
    if os.path.exists(file_path):
        data= pd.read_excel(file_path,parse_dates=['Report Date'])
        return data
    else:
        st.error(f"Source data file not found: {file_path}")
        return None

# Function to create the top container with filters
def create_top_container(data):
    col1, col2, col3, col4,col5 = st.columns([2,1,1,2,2])
    
    with col1:
        st.subheader("Select Category")
        categories = data['Category'].unique().tolist()
        selected_categories = st.multiselect("Categories", categories)
        
    # Calculate min and max dates from the data
    min_date = data['Report Date'].min().strftime('%d/%m/%Y')
    max_date = data['Report Date'].max().strftime('%d/%m/%Y')        
    with col2:
        st.subheader("Date")
        selected_date_from = st.date_input("From Date", value=datetime.strptime(min_date, '%d/%m/%Y').date(), min_value=datetime.strptime(min_date, '%d/%m/%Y').date(), max_value=datetime.strptime(max_date, '%d/%m/%Y').date())
        selected_date_from = selected_date_from.strftime('%d/%m/%Y')

    with col3:
        st.subheader(" ")
        selected_date_to = st.date_input("To Date", value=datetime.strptime(max_date, '%d/%m/%Y').date(), min_value=datetime.strptime(min_date, '%d/%m/%Y').date(), max_value=datetime.strptime(max_date, '%d/%m/%Y').date())
        selected_date_to = selected_date_to.strftime('%d/%m/%Y')
        
    with col4:
        st.subheader("Select Platform")
        platforms = data['Platform'].unique().tolist()
        selected_platforms = st.multiselect("Platforms", platforms)
        
    with col5:
        st.subheader("Select City")
        cities = data['City'].unique().tolist()
        selected_cities = st.multiselect("Cities", cities)
        
    return selected_categories, selected_date_from,selected_date_to, selected_platforms, selected_cities


# Function to create the bottom container with plots
def bottom_container(filtered_data):
    col1, col2, col3 = st.columns([1,2,2])
    
    with col1:
        st.subheader("Select Product")
        if filtered_data is not None:
            products = filtered_data['Product Description'].unique().tolist()
            selected_products = st.multiselect("Products", products)
        else:
            selected_products = []
        # Apply product filter
        if selected_products:
            filtered_data_with_products = filtered_data[filtered_data['Product Description'].isin(selected_products)]
        else:
            filtered_data_with_products = filtered_data
        
    with col2:
        try:
            st.subheader("Availability Percent and Avg Discount Percent by Brand")
            if filtered_data_with_products is not None and 'Discount' in filtered_data_with_products.columns and 'Stock Availability (Y/N)' in filtered_data_with_products.columns:
                # Ensure Discount column is in percentage format
                filtered_data_with_products['Discount'] = pd.to_numeric(filtered_data_with_products['Discount'].str.replace('%', ''), errors='coerce')
                
                # Calculate average discount percentage
                avg_discount = filtered_data_with_products.groupby('Brand Name')['Discount'].mean().reset_index()
                
                # Calculate availability percentage for each brand
                availability_percentage = filtered_data_with_products.groupby('Brand Name')['Stock Availability (Y/N)'].apply(
                    lambda x: (x[x == 'Yes'].count() / x[x != ''].count()) * 100
                ).reset_index(name='Availability Percentage')
                availability_percentage.columns = ['Brand Name', 'Availability Percentage']
                
                # st.write(availability_percentage)
                # Merge the two dataframes
                merged_data = pd.merge(avg_discount, availability_percentage, on='Brand Name')
                
                # Grouped bar chart for discount and availability by brand
                fig = px.bar(
                    merged_data,
                    x='Brand Name',
                    y=['Discount', 'Availability Percentage'],
                    barmode='group',
                    # title='Availability Percent and Avg Discount Percent by Brand'
                )
                
                # Update the layout to show values on the bars
                fig.update_traces(texttemplate='%{y:.2f}', textposition='outside')
                    
                st.plotly_chart(fig)
            else:
                st.warning("No data available for the selected product.")
        except Exception as e:
            print(e)
            st.warning("No data available for the selected product.")
    with col3:
        st.subheader("Avg Selling Price and Avg MRP by Brand")
        filtered_data=filtered_data_with_products
        # Rename the column to remove special symbols
        filtered_data.rename(columns={'MRP (₹)': 'MRP'}, inplace=True)
        if filtered_data is not None and 'Selling Price' in filtered_data.columns and 'MRP' in filtered_data.columns:
            # Group by 'Brand Name' and calculate the mean of 'Selling Price' and 'MRP'
            avg_price_by_brand = filtered_data.groupby('Brand Name')[['Selling Price', 'MRP']].mean().reset_index()
            
            # Create a bar chart using plotly.express
            fig = px.bar(avg_price_by_brand, x='Brand Name', y=['Selling Price', 'MRP'], barmode='group', 
                        title='Avg Selling Price and Avg MRP by Brand')
            
            # Update the layout to show values on the bars
            fig.update_traces(texttemplate='%{y:.2f}', textposition='outside')
            
            # Display the chart in Streamlit
            st.plotly_chart(fig)
        else:
            st.warning("No selling price data available.")
# Main function to run the app
def run():
    global data
    data = load_data("data/competition.xlsx")
    
    if data is not None:
        selected_categories, selected_date_f,selected_date_t, selected_platforms, selected_cities = create_top_container(data)
        
        # Filter data based on selected options
        filtered_data = data.copy()
        if selected_categories:
            filtered_data = filtered_data[filtered_data['Category'].isin(selected_categories)]
        if selected_date_f and selected_date_t:
            filtered_data = filtered_data[(filtered_data['Report Date'] >= selected_date_f) & (filtered_data['Report Date'] <= selected_date_t)]
        if selected_platforms:
            filtered_data = filtered_data[filtered_data['Platform'].isin(selected_platforms)]
        if selected_cities:
            filtered_data = filtered_data[filtered_data['City'].isin(selected_cities)]
        
        selected_products = bottom_container(filtered_data)
        
        # Further filter data based on selected products
        if selected_products:
            filtered_data = filtered_data[filtered_data['Product Description'].isin(selected_products)]
        
        # Display filtered data
        # st.write(filtered_data)

    # Footer
    st.markdown("**Powered by Purple Block**")

if __name__ == "__main__":
    run()