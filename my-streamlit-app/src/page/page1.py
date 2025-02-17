import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import os
import numpy as np


class DataLoader:
    """Handles loading and processing of data from an Excel file and related sources."""

    def __init__(self, file_path: str, city_data_path: str, map_data_path: str):
        self.file_path = file_path
        self.city_data_path = city_data_path
        self.map_data_path = map_data_path
        self.data = None

    def load_data(self):
        """Loads the product data from an Excel file."""
        if not os.path.exists(self.file_path):
            st.error(f"File not found: {self.file_path}")
            return None
        self.data = pd.read_excel(self.file_path)
        return self.data

    def load_city_data(self):
        """Loads city latitude and longitude data."""
        if not os.path.exists(self.city_data_path):
            st.error(f"City data file not found: {self.city_data_path}")
            return None
        return pd.read_csv(self.city_data_path, encoding="utf-8")

    def load_map_data(self):
        """Loads the world map data for India."""
        if not os.path.exists(self.map_data_path):
            st.error(f"Map data file not found: {self.map_data_path}")
            return None
        world = gpd.read_file(self.map_data_path)
        india_map = world[world.ADMIN == "India"]
        return india_map


class MapGenerator:
    """Generates and displays interactive maps based on the availability data."""

    def __init__(self, data, city_data, map_data):
        self.data = data
        self.city_data = city_data
        self.map_data = map_data

    def calculate_availability(self, product_filter=None):
        """Calculates the product availability percentage by city."""

        if product_filter:
            # Filter data based on product description
            df = self.data[self.data['Product Description'] == product_filter].copy()
            df['available'] = df['Stock Availability (Y/N)'].apply(lambda x: 1 if x == 'Yes' else 0)

            # Step 3: Group by city and calculate the mean availability (percentage)
            availability_df = df.groupby('City')['available'].mean().reset_index()

            # Step 4: Multiply the mean availability by 100 to get the percentage
            availability_df['availability_percentage'] = availability_df['available'] * 100

            # Step to round up the availability percentage to 2 decimal places
            availability_df['availability_percentage']=availability_df['availability_percentage'].round(2)

            # Step 5: Merge with city latitude and longitude data (if available)
            availability_df = availability_df.merge(self.city_data, left_on="City", right_on="city", how="left")

            # Step 6: Drop the duplicate 'city' column after merge
            availability_df.drop(columns=["city"], inplace=True)

            # Step 7: Drop rows with missing values (NaN) from the merged data
            # This is especially important after merging with the city data since some cities may not have lat/lng info
            # availability_df.dropna(inplace=True)

            return availability_df
            
        else:
            # Convert data to DataFrame
            df = pd.DataFrame(self.data)

            # Step 1: Replace missing values in 'Stock Availability (Y/N)' with 'No'
            # This assumes missing values indicate 'No' availability (you can customize this assumption if needed).
            df['Stock Availability (Y/N)'].fillna('No', inplace=True)

            # Step 2: Convert 'Stock Availability (Y/N)' to binary values (1 for 'Yes', 0 for 'No')
            df['available'] = df['Stock Availability (Y/N)'].apply(lambda x: 1 if x == 'Yes' else 0)

            # Step 3: Group by city and calculate the mean availability (percentage)
            availability_df = df.groupby('City')['available'].mean().reset_index()

            # Step 4: Multiply the mean availability by 100 to get the percentage
            availability_df['availability_percentage'] = availability_df['available'] * 100

            # Step 5: Merge with city latitude and longitude data (if available)
            availability_df = availability_df.merge(self.city_data, left_on="City", right_on="city", how="left")

            print("Checking for Pune",availability_df[availability_df['City'] == "Pune"])

            # Step 6: Drop the duplicate 'city' column after merge
            availability_df.drop(columns=["city"], inplace=True)

            print("Checking for Pune after column drop",availability_df[availability_df['City'] == "Pune"])

            # Step 7: Drop rows with missing values (NaN) from the merged data
            # This is especially important after merging with the city data since some cities may not have lat/lng info
            # availability_df.dropna(inplace=True)


            return availability_df

    def generate_map(self, availability_df, product_filter=None):
        """Generates a plotly map showing availability by city."""
        fig = px.scatter_mapbox(
            availability_df,
            lat="lat",
            lon="lng",
            size="availability_percentage",
            color="availability_percentage",
            color_continuous_scale="Viridis",
            hover_name="City",
            mapbox_style="open-street-map",
            zoom=4,
            height=600
        )

        title = f"Product Availability Percentage in India by City ({product_filter if product_filter else 'All Products'})"
        fig.update_layout(
            title=title,
            margin={"r": 0, "t": 40, "l": 0, "b": 0}
        )

        return fig


class UI:
    """Handles the user interface components in Streamlit."""

    def __init__(self, data_loader: DataLoader, map_generator: MapGenerator):
        self.data_loader = data_loader
        self.map_generator = map_generator

    def display_heading(self):
        """Displays the heading of the dashboard."""
        st.subheader("Bikagi Project Dashboard")

    def display_data(self):
        """Displays the raw data as a DataFrame."""
        st.dataframe(self.data_loader.data)

    def display_product_selector(self, unique_products):
        """Displays a scrollable list of product buttons (converted to dropdown or radio)."""
        st.write("### Select a Product to Filter")

        # Using a selectbox for scrollable selection
        selected_product = st.selectbox("Choose a Product", unique_products)

        return selected_product

    def display_map(self, product_filter=None):
        """Displays the generated map based on product selection."""
        # Calculate availability data and generate map
        availability_df = self.map_generator.calculate_availability(product_filter)
        fig = self.map_generator.generate_map(availability_df, product_filter)
        st.plotly_chart(fig)


class HeatmapApp:
    """Main app that integrates the data, map generation, and UI components."""

    def __init__(self, file_path: str, city_data_path: str, map_data_path: str):
        self.data_loader = DataLoader(file_path, city_data_path, map_data_path)
        self.map_generator = None
        self.ui = None

    def run(self):
        """Runs the entire app."""
        st.title("📊 Heatmap Visualization")

        # Load data
        data = self.data_loader.load_data()
        if data is not None:
            self.map_generator = MapGenerator(data, self.data_loader.load_city_data(), self.data_loader.load_map_data())
            self.ui = UI(self.data_loader, self.map_generator)

            # Display heading and raw data
            self.ui.display_heading()

            # Get unique products from the data and display product selector
            unique_products = self.data_loader.data['Product Description'].unique()

            # Prepend "All Products"
            unique_products = np.insert(unique_products, 0, "All Products")
            selected_product = self.ui.display_product_selector(unique_products)

            # Display the map based on selected product
            if selected_product and selected_product != "All Products":
                st.write(f"Showing availability for: **{selected_product}**")
                self.ui.display_map(product_filter=selected_product)
            else:
                st.write("Showing availability for **all products**")
                self.ui.display_map()


def main():
    file_path = os.path.join("data", "competition.xlsx")
    city_data_path = "maps/india_city.csv"
    map_data_path = "maps/ne_110m_admin_0_countries.shp"
    
    app = HeatmapApp(file_path, city_data_path, map_data_path)
    app.run()


if __name__ == "__main__":
    main()
