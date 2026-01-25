from pystac_client import Client
import planetary_computer
import rasterio
from rasterio.io import MemoryFile
from rasterio.merge import merge
from rasterio.mask import mask
import numpy as np
from datetime import timedelta

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"

def find_images(bbox, date_range="2023-01-01/2023-12-31", cloud=10):
    catalog = Client.open(STAC_URL, modifier=planetary_computer.sign_inplace)
    
    s = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=bbox,
        datetime=date_range,
        query={"eo:cloud_cover": {"lt": cloud}},
        sortby=[{"field": "eo:cloud_cover", "direction": "asc"}]
    )
    
    res = s.item_collection()
    print("images found:", len(res))
    return res

def sort_images(items):
    if len(items) == 0:
        return []
        
    best = items[0]
    d = best.datetime
    
    final_list = []
    for i in items:
        if abs(i.datetime - d) < timedelta(hours=2):
            final_list.append(i)
            
    print("using", len(final_list), "tiles from date", d.date())
    return final_list

def get_band(items, band, s=0.25):
    if not items:
        return None, None

    from rasterio.vrt import WarpedVRT
    
    temp = []
    tomerge = []
    
    def process(ds, crs):
        h = int(ds.height * s)
        w = int(ds.width * s)
        
        if h == 0 or w == 0:
            return 
            
        d = ds.read(
            1,
            out_shape=(h, w),
            resampling=rasterio.enums.Resampling.bilinear
        )
        
        trans = ds.transform * ds.transform.scale(
            (ds.width / d.shape[-1]),
            (ds.height / d.shape[-2])
        )
        
        m = MemoryFile()
        dst = m.open(
            driver='GTiff',
            height=h,
            width=w,
            count=1,
            dtype=d.dtype,
            crs=crs,
            transform=trans,
        )
        dst.write(d, 1)
        return m, dst

    item1 = items[0]
    link1 = item1.assets[band].href
    
    with rasterio.open(link1) as f1:
        crs1 = f1.crs
        m, d = process(f1, crs1)
        temp.append(m)
        tomerge.append(d)
        
    for i in items[1:]:
        link = i.assets[band].href
        try:
            with rasterio.open(link) as f:
                if f.crs != crs1:
                   with WarpedVRT(f, crs=crs1) as vrt:
                       m, d = process(vrt, crs1)
                else:
                    m, d = process(f, crs1)
                
                temp.append(m)
                tomerge.append(d)
        except Exception as e:
            print("error:", e)
            continue

    if len(tomerge) == 0:
        return None, None

    print("merging tiles...")
    img, trans = merge(tomerge)
    
    for x in temp: 
        x.close()
    
    prof = {
        "transform": trans,
        "height": img.shape[1],
        "width": img.shape[2],
        "crs": crs1,
        "count": 1
    }
    
    return img[0], prof

def crop_data(arr, trans, shapes, crop=True):
    from rasterio.features import geometry_mask
    
    r, c = arr.shape
    
    m = geometry_mask(
        shapes,
        transform=trans,
        invert=True,
        out_shape=(r, c)
    )
    
    arr = arr.astype(float)
    arr[~m] = np.nan
    
    if crop:
        with MemoryFile() as mf:
            with mf.open(
                driver='GTiff',
                height=r,
                width=c,
                count=1,
                dtype=arr.dtype,
                crs=None,
                transform=trans,
            ) as dst:
                dst.write(arr, 1)
                
            with mf.open() as src:
                out, out_trans = mask(src, shapes, crop=True, nodata=np.nan)
        
        return out[0], out_trans
        
    return arr, trans

if __name__ == "__main__":
    b = [77.10, 28.50, 77.30, 28.70] 
    res = find_images(b, date_range="2023-01-01/2023-01-30")
    
    if len(res) > 0:
        print("got it")
