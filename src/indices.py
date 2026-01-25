import numpy as np

def calculate_ndvi(red, nir):
    np.seterr(all='ignore')
    
    val = (nir - red) / (nir + red)
    return val

def calculate_ndbi(swir, nir):
    np.seterr(all='ignore')
    
    val = (swir - nir) / (swir + nir)
    return val

def normalize(arr):
    mn = np.nanmin(arr)
    mx = np.nanmax(arr)
    return (arr - mn) / (mx - mn)
