import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

def create_top_container(data):
    # Create four containers in the first row
    col1, col2, col3, col4 , col5 = st.columns([2,2,2,1,1])
    
    with col1:
        st.subheader("Select Category")
        categories = data['Category'].unique().tolist()
        selected_categories = st.multiselect("Categories", categories)
        
    with col2:
        st.subheader("Select Platform")
        if selected_categories:
            filtered_data = data[data['Category'].isin(selected_categories)]
            platforms = filtered_data['Platform'].unique().tolist()
        else:
            platforms = data['Platform'].unique().tolist()
        selected_platforms = st.multiselect("Platforms", platforms)
        
    with col3:
        st.subheader("Select City")
        if selected_platforms:
            filtered_data = data[data['Platform'].isin(selected_platforms)]
            cities = filtered_data['City'].unique().tolist()
        else:
            cities = data['City'].unique().tolist()
        selected_cities = st.multiselect("Cities", cities)
        
     # Calculate min and max dates from the data
    min_date = data['Report Date'].min().strftime('%d/%m/%Y')
    max_date = data['Report Date'].max().strftime('%d/%m/%Y')    
    # with col4:
    #     st.subheader("Select Date From")
    #     selected_date_f = st.date_input("From Date", value=datetime.strptime(min_date, '%d/%m/%Y').date())
    #     selected_date_from = selected_date_f.strftime('%d/%m/%Y')
        
    # with col4:
    #     st.subheader("Select Date To")
    #     selected_date_to = st.date_input("To Date", value=datetime.strptime(max_date, '%d/%m/%Y').date())
    #     selected_date_to = selected_date_to.strftime('%d/%m/%Y')
    with col4:
        st.subheader("Date")       
        # col4_1, col4_2 = st.columns(2)
        # with col4_1:
            # st.subheader("Date Selector")
        selected_date_from = st.date_input("From Date", value=datetime.strptime(min_date, '%d/%m/%Y').date(), min_value=datetime.strptime(min_date, '%d/%m/%Y').date(), max_value=datetime.strptime(max_date, '%d/%m/%Y').date())
        selected_date_from = selected_date_from.strftime('%d/%m/%Y')
    with col5:        
        # with col4_2:
        st.subheader("")
        selected_date_to = st.date_input("To Date", value=datetime.strptime(max_date, '%d/%m/%Y').date(), min_value=datetime.strptime(min_date, '%d/%m/%Y').date(), max_value=datetime.strptime(max_date, '%d/%m/%Y').date())
        selected_date_to = selected_date_to.strftime('%d/%m/%Y')
        
    return selected_categories, selected_platforms, selected_cities, selected_date_from,selected_date_to


def bottom_container(filtered_data):
    # Create three containers in the second row
    col1, col2, col3 = st.columns([1, 2, 2])
    
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
        st.subheader("Average Discount Percentage and Availability Graph")
        if not filtered_data_with_products.empty:
            # Calculate average discount percentage
            avg_discount = filtered_data_with_products.groupby('Platform')['Discount'].mean().reset_index()

            # Calculate availability percentage
            # N O T E ::::: Here i have ignored empty cell from calculation
            availability = filtered_data_with_products.groupby('Platform')['Stock Availability (Y/N)'].apply(
                lambda x: (x[x == 'Yes'].count() / x[x != ''].count()) * 100
            ).reset_index(name='Availability')

            # Merge the two dataframes
            merged_data = pd.merge(avg_discount, availability, on='Platform')

            # Create a grouped bar chart
            fig = px.bar(merged_data, x='Platform', y=['Discount', 'Availability'], 
                barmode='group', title='Average Discount Percentage and Availability by Platform',labels={'value': 'Percentage'})
            
            # Update the layout to show values on the bars
            fig.update_traces(texttemplate='%{y:.2f}%', textposition='outside')

            st.plotly_chart(fig)
        else:
            st.warning("No data available for the selected product.")   
        
    
    with col3:
        st.subheader("Selling Price Trend")
        if not filtered_data.empty and 'Selling Price' in filtered_data.columns:
            # Filter out rows with empty Selling Price values
            filtered_data = filtered_data.dropna(subset=['Selling Price'])
            # Extract year and quarter from 'Report Date' for the x-axis
            filtered_data['Year'] = filtered_data['Report Date'].dt.year
            filtered_data['Quarter'] = filtered_data['Report Date'].dt.quarter
            # st.write("Trend data:", filtered_data)
            # Create a Plotly line chart with quarters on the x-axis
            price_fig = px.line(filtered_data, x='Year', y='Selling Price', color='Quarter', title='Selling Price Trend by Quarter')
            
            # Display the chart in Streamlit
            st.plotly_chart(price_fig)
        else:
            st.warning("No data available for the selected product.")
    
    return selected_products

@st.cache_data
def load_data(file_path):
    if os.path.exists(file_path):
        data= pd.read_excel(file_path,parse_dates=['Report Date'])
        return data
    else:
        st.error(f"Source data file not found: {file_path}")
        return None

def run():
    global data
    data = load_data("data/competition.xlsx")
    data['Discount'] = data['Discount'].str.replace("%", "").astype(float)

    if data is not None:
        selected_categories, selected_platforms, selected_cities, selected_date_from,selected_date_to = create_top_container(data)
        
        # Filter data based on selected options
        filtered_data = data.copy()
        if selected_date_from and selected_date_to:
            filtered_data = filtered_data[(filtered_data['Report Date'] >= selected_date_from) & (filtered_data['Report Date'] <= selected_date_to)]
        if selected_categories:
            filtered_data = filtered_data[filtered_data['Category'].isin(selected_categories)]
        if selected_platforms:
            filtered_data = filtered_data[filtered_data['Platform'].isin(selected_platforms)]
        if selected_cities:
            filtered_data = filtered_data[filtered_data['City'].isin(selected_cities)]
        print("Selected date from:",selected_date_from)
        
       
        st.empty()

        # Further filter data based on selected products
        selected_products = bottom_container(filtered_data)
        if selected_products:
            filtered_data = filtered_data[filtered_data['Product Description'].isin(selected_products)]
        
        # Display filtered data
        # st.write(filtered_data)

    # Footer
    st.markdown("**Powered by Purple Block**")

if __name__ == "__main__":
    run()