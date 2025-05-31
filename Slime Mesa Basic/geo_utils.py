import geopandas as gpd
import os

def load_stations(path):
    stations = gpd.read_file(path)

    # Extract lon/lat
    stations['lon'], stations['lat'] = stations.geometry.x, stations.geometry.y
    stations['value'] = 4
    
    min_lon = stations['lon'].min()
    min_lat = stations['lat'].min()
    
    # Scale to grid
    stations['x'] = ((stations['lon'] - min_lon) * 1000).astype(int)
    stations['y'] = ((stations['lat'] - min_lat) * 1000).astype(int)
    
    # Normalize to top-left origin + padding
    min_x = stations['x'].min()
    min_y = stations['y'].min()
    stations['x'] = (stations['x'] - min_x + 10).astype(int)
    stations['y'] = (stations['y'] - min_y + 10).astype(int)
    
    # Deduplicate
    stations['nodes'] = stations[['x', 'y']].apply(tuple, axis=1)
    stations = stations.drop_duplicates(subset=['nodes'])

    return stations[['nodes']]

