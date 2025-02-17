import pandas as pd
import geopandas as gpd
import plotly.express as px

# Load Indian Cities dataset (Make sure this CSV exists in your directory)
city_data = pd.read_csv("maps/india_city.csv")  # City, State, Latitude, Longitude

# Sample Product Availability Data
data = {
    'city': ['New Delhi', 'Bengaluru', 'Mumbai', 'Chennai', 'Kolkata', 'Hyderabad'],
    'product': ['Product A'] * 6,
    'availability': ['YES', 'NO', 'YES', 'YES', 'NO', 'YES']  # YES or NO
}
df = pd.DataFrame(data)

# Calculate Availability Percentage
df['available'] = df['availability'].apply(lambda x: 1 if x == 'YES' else 0)
availability_df = df.groupby('city')['available'].mean().reset_index()
availability_df['availability_percentage'] = availability_df['available'] * 100

# Merge with City Coordinates
merged_df = availability_df.merge(city_data, on="city", how="left")
merged_df.dropna(subset=["lat", "lng"], inplace=True)  # Remove missing values

# Load India GeoJSON map
world = gpd.read_file("maps/ne_110m_admin_0_countries.shp")
india_map = world[world.ADMIN == "India"]# Filter for India

# Create an Interactive Bubble Map
fig = px.scatter_mapbox(
    merged_df,
    lat="lat",
    lon="lng",
    size="availability_percentage",
    color="availability_percentage",
    color_continuous_scale="Viridis",
    hover_name="city",
    hover_data={"availability_percentage": True, "lat": False, "lng": False},
    size_max=40,
    title="Product Availability Percentage in Indian Cities"
)

# Set Map Style
fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_zoom=4,
    mapbox_center={"lat": 20.5937, "lon": 78.9629},  # Center India
    margin={"r": 0, "t": 40, "l": 0, "b": 0}
)

fig.show()
