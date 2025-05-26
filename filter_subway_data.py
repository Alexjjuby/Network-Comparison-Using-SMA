import pandas as pd
import geopandas as gpd

# === File paths (adjust these as needed) ===
routes_file = "Rome Data/routes.geojson"
stops_file = "Rome Data/stops.geojson"
subway_csv_file = "Rome Data/network_rail.csv"

# === Load GeoJSON data ===
print("📥 Loading route and stop data...")
routes_gdf = gpd.read_file(routes_file)
stops_gdf = gpd.read_file(stops_file)

# === Load subway CSV data ===
print("📥 Loading subway link data...")
subway_df = pd.read_csv(subway_csv_file, sep=';', engine='python')
subway_df.columns = subway_df.columns.str.strip()  # remove leading/trailing whitespace

# === Get all relevant stop IDs used in the subway network ===
print("🔍 Extracting relevant stop IDs...")
subway_stop_ids = pd.unique(subway_df[['from_stop_I', 'to_stop_I']].values.ravel())

# === Get all route_I values mentioned in route_I_counts ===
def extract_route_ids(route_str):
    ids = []
    for entry in str(route_str).split(','):
        if ':' in entry:
            try:
                route_id = int(entry.split(':')[0])
                ids.append(route_id)
            except ValueError:
                continue
    return ids

print("🔍 Extracting relevant route IDs...")
all_route_ids = set()
subway_df['route_I_counts'].dropna().apply(lambda x: all_route_ids.update(extract_route_ids(x)))

# === Filter routes and stops ===
print("🔎 Filtering route and stop data...")
routes_gdf['route_I'] = routes_gdf['route_I'].astype(int)
filtered_routes = routes_gdf[routes_gdf['route_I'].isin(all_route_ids)]

stops_gdf['stop_I'] = stops_gdf['stop_I'].astype(int)
filtered_stops = stops_gdf[stops_gdf['stop_I'].isin(subway_stop_ids)]

# === Save the filtered GeoJSONs ===
print("💾 Saving filtered data...")
filtered_routes.to_file("rome_rail_routes.geojson", driver="GeoJSON")
filtered_stops.to_file("rome_rail_stops.geojson", driver="GeoJSON")

print("✅ Done! Filtered subway data saved as:")
print("  - subway_routes.geojson")
print("  - subway_stops.geojson")
