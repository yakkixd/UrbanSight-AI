import os
import matplotlib.pyplot as plt
import numpy as np
from data_loader import load_districts
from sentinel_client import find_images, sort_images, get_band, crop_data
from indices import calculate_ndvi, calculate_ndbi, normalize

def do_processing(d_name, shp_path):
    data = load_districts(shp_path)
    
    d = data[data['d_name'] == d_name]
    if d.empty:
        print("district not found")
        return None
        
    print("starting for", d_name)
    
    b = d.total_bounds
    bbox = [b[0], b[1], b[2], b[3]]
    
    print("searching images...")
    items = find_images(bbox, date_range="2023-01-01/2023-05-30")
    if len(items) == 0:
        print("no images")
        return None
        
    tiles = sort_images(items)
    
    s = 0.2
    
    print("getting bands...")
    red, prof = get_band(tiles, "B04", s=s)
    
    nir, _ = get_band(tiles, "B08", s=s)
    swir, _ = get_band(tiles, "B11", s=s)
    
    target = red.shape
    print("shape is:", target)
    
    def fix_size(arr, t, n):
        if arr.shape != t:
            print("resizing", n)
            from scipy.ndimage import zoom
            z1 = t[0] / arr.shape[0]
            z2 = t[1] / arr.shape[1]
            return zoom(arr, (z1, z2), order=0)
        return arr

    nir = fix_size(nir, target, "NIR")
    swir = fix_size(swir, target, "SWIR")
    
    print("clipping data...")
    crs = prof['crs']
    d_proj = d.to_crs(crs)
    geoms = d_proj.geometry.values
    
    trans = prof['transform']
    red, out_trans = crop_data(red, trans, geoms, crop=True)
    prof['transform'] = out_trans
    
    new_shape = red.shape
    print("new shape:", new_shape)

    nir, _ = crop_data(nir, trans, geoms, crop=True)
    swir, _ = crop_data(swir, trans, geoms, crop=True)
    
    nir = fix_size(nir, new_shape, "NIR Masked")
    swir = fix_size(swir, new_shape, "SWIR Masked")
    
    mask = (red > 0) & (nir > 0) & (~np.isnan(red))
    
    red = red.astype(float)
    nir = nir.astype(float)
    swir = swir.astype(float)
    
    red[~mask] = np.nan
    nir[~mask] = np.nan
    swir[~mask] = np.nan
        
    print("calculating indices...")
    ndvi = calculate_ndvi(red, nir)
    ndbi = calculate_ndbi(swir, nir)
    
    slums = (ndbi > 0.05) & (ndvi < 0.3)
    
    return ndvi, ndbi, slums, prof

def run_main(name, path, out="output"):
    res = do_processing(name, path)
    if res is None:
        return
        
    ndvi, ndbi, slums, prof = res
    
    print("stats for ndvi:", np.nanmean(ndvi))
    print("stats for ndbi:", np.nanmean(ndbi))
    
    if not os.path.exists(out):
        os.makedirs(out)
        
    plt.figure(figsize=(15, 5))
    
    plt.subplot(1, 3, 1)
    plt.title("NDVI")
    plt.imshow(ndvi, cmap='RdYlGn', vmin=-1, vmax=1)
    
    plt.subplot(1, 3, 2)
    plt.title("NDBI")
    plt.imshow(ndbi, cmap='gray', vmin=-1, vmax=1)
    
    plt.subplot(1, 3, 3)
    plt.title("Sprawl")
    plt.imshow(slums, cmap='Reds')
    
    fname = os.path.join(out, f"{name}_res.png")
    plt.savefig(fname)
    print("saved to", fname)
    plt.close()

if __name__ == "__main__":
    import argparse
    
    p = argparse.ArgumentParser()
    p.add_argument("--district", type=str, default="Mahesana")
    p.add_argument("--shapefile", type=str, default="data/district.shp")
    
    a = p.parse_args()
    
    run_main(a.district, a.shapefile)
