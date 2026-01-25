import geopandas as gpd
import os

def load_districts(path):
    if not os.path.exists(path):
        print("file not found")
        return None
    
    print("reading shapefile...")
    df = gpd.read_file(path)
    print("done, loaded", len(df), "rows")
    
    return df

if __name__ == "__main__":
    p = path if path else "data/district.shp"
    load_districts(p)
