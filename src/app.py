import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis import do_processing
from data_loader import load_districts

st.set_page_config(page_title="UrbanSight AI", layout="wide")

st.title("🏙️ UrbanSight Project")
st.markdown("Monitoring Urban Sprawl and Slums in India")

def load_css(fname):
    with open(fname) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

try:
    load_css("urban_sprawl_project/src/style.css")
except:
    pass 

# Logic to find the data relative to the repo root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
SHP_PATH = os.path.join(DATA_DIR, "district.shp")
STATS = os.path.join(os.path.dirname(__file__), "district_stats.csv")

@st.cache_data
def get_data():
    data = load_districts(SHP_PATH)
    data['geometry'] = data['geometry'].simplify(0.002)
    
    if os.path.exists(STATS):
        df = pd.read_csv(STATS)
        data = data.merge(df, on="d_name", how="left")
    else:
        st.warning("No stats file found.")
        data['mean_ndvi'] = 0
        data['mean_ndbi'] = 0
        data['sprawl_risk'] = 0
        
    return data

try:
    with st.spinner("Loading Data..."):
        data = get_data()
        d_list = sorted(data['d_name'].dropna().unique())
except Exception as e:
    st.error(f"Error: {e}")
    st.stop()

if "place" not in st.session_state:
    st.session_state.place = "Agra"

def update_side():
    st.session_state.place = st.session_state.selector

st.sidebar.header("Navigation")

try:
    idx = d_list.index(st.session_state.place)
except:
    idx = 0

sel = st.sidebar.selectbox(
    "Select District", 
    d_list, 
    index=idx,
    key="selector",
    on_change=update_side
)

st.markdown("### Map View")

data['sprawl_risk'] = data['sprawl_risk'].fillna(0)
data['safety'] = 100 - data['sprawl_risk']

m = folium.Map(
    location=[22.0, 79.0], 
    zoom_start=5, 
    min_zoom=4,
    max_bounds=True,
    tiles="CartoDB positron"
)

m.fit_bounds([[6.0, 68.0], [37.0, 97.0]])

data['id'] = data.index.astype(str)
c_data = data.copy()

folium.Choropleth(
    geo_data=data.__geo_interface__,
    name="Urban Health",
    data=c_data,
    columns=['id', 'safety'],
    key_on="feature.id",
    fill_color='RdYlGn', 
    fill_opacity=0.7,
    line_opacity=0.1,
    legend_name="Safety Score",
    nan_fill_color="white"
).add_to(m)

folium.GeoJson(
    data,
    name="Interaction",
    style_function=lambda x: {'fillColor': '#00000000', 'color': '#00000000'},
    highlight_function=lambda x: {'fillColor': '#00000000', 'color': '#000000', 'weight': 2},
    tooltip=folium.GeoJsonTooltip(
        fields=['d_name', 'mean_ndvi', 'mean_ndbi', 'sprawl_risk'],
        aliases=['District:', 'Green:', 'Urban:', 'Risk %:'],
        localize=True
    )
).add_to(m)

if st.session_state.place:
    sel_geom = data[data['d_name'] == st.session_state.place]
    
    if not sel_geom.empty:
        folium.GeoJson(
            sel_geom,
            name="Selected",
            style_function=lambda x: {'fillColor': '#00000000', 'color': 'blue', 'weight': 5}
        ).add_to(m)
        
        b = sel_geom.total_bounds
        m.fit_bounds([[b[1], b[0]], [b[3], b[2]]])

st_data = st_folium(m, width=1200, height=500, returned_objects=["last_object_clicked"])

if st_data and st_data.get("last_object_clicked"):
    props = st_data["last_object_clicked"].get("properties")
    if props and "d_name" in props:
        clicked = props["d_name"]
        if clicked != st.session_state.place:
            st.session_state.place = clicked
            st.rerun()

place = st.session_state.place

st.markdown("---")
st.header(f"Analysis for: {place}")

def check_val(val, type):
    if type == 'ndvi':
        if val > 0.4: return "Very Green"
        if val > 0.2: return "Okay Green"
        return "Low Green"
    if type == 'ndbi':
        if val > 0.1: return "High Urban"
        if val > -0.1: return "Medium Urban"
        return "Low Urban"
    if type == 'risk':
        if val > 50: return "High Risk"
        if val > 20: return "Medium Risk"
        return "Low Risk"

stats = data[data['d_name'] == place].iloc[0]

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Green Score", f"{stats['mean_ndvi']:.2f}")
    st.write(check_val(stats['mean_ndvi'], 'ndvi'))
    
with c2:
    st.metric("Concrete Score", f"{stats['mean_ndbi']:.2f}")
    st.write(check_val(stats['mean_ndbi'], 'ndbi'))
    
with c3:
    st.metric("Risk %", f"{stats['sprawl_risk']:.1f}%")
    st.write(check_val(stats['sprawl_risk'], 'risk'))

st.subheader("Growth Prediction")

np.random.seed(int(stats['mean_ndvi']*100)) 
yrs = ["2019", "2020", "2021", "2022", "2023"] 
base = stats['mean_ndbi'] if stats['mean_ndbi'] > 0 else 0.1
rate = stats['sprawl_risk'] / 500

vals = []
curr = base
for i in yrs:
    n = np.random.uniform(-0.02, 0.05)
    curr += (curr * rate) + n
    vals.append(curr)
    
chart = pd.DataFrame({"Year": yrs, "Value": vals})
st.line_chart(chart, x="Year", y="Value")

if st.button(f"Analyze {place} (Real Data)", type="primary"):
    st.write("---")
    st.info(f"Fetching Sentinel-2 data for {place}...")
    
    with st.spinner("Processing..."):
        try:
            res = do_processing(place, SHP_PATH)
        except Exception as e:
            st.error(f"Error: {e}")
            res = None
            
    if res is None:
        st.error("Failed to get data.")
    else:
        ndvi, ndbi, slums, prof = res
        
        st.success("Done!")
        st.markdown("### Results")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader("NDVI")
            fig1, ax1 = plt.subplots(figsize=(4,4))
            ax1.imshow(ndvi, cmap='RdYlGn', vmin=-1, vmax=1)
            ax1.axis('off')
            st.pyplot(fig1)
            
        with col2:
            st.subheader("NDBI")
            fig2, ax2 = plt.subplots(figsize=(4,4))
            ax2.imshow(ndbi, cmap='gray', vmin=-1, vmax=1)
            ax2.axis('off')
            st.pyplot(fig2)
            
        with col3:
            st.subheader("Risk Areas")
            fig3, ax3 = plt.subplots(figsize=(4,4))
            ax3.imshow(ndbi, cmap='gray', alpha=0.5)
            mask = np.ma.masked_where(slums == 0, slums)
            ax3.imshow(mask, cmap='Reds', vmin=0, vmax=1)
            ax3.axis('off')
            st.pyplot(fig3)
            
        st.write("Histograms")
        h1, h2 = st.columns(2)
        
        with h1:
            st.write("NDVI Dist")
            v1 = ndvi.flatten()
            v1 = v1[~np.isnan(v1)]
            hist, edges = np.histogram(v1, bins=20, range=(-1, 1))
            st.bar_chart(pd.DataFrame({"Val": edges[:-1], "Freq": hist}).set_index("Val"))
            
        with h2:
            st.write("NDBI Dist")
            v2 = ndbi.flatten()
            v2 = v2[~np.isnan(v2)]
            hist2, edges2 = np.histogram(v2, bins=20, range=(-1, 1))
            st.bar_chart(pd.DataFrame({"Val": edges2[:-1], "Freq": hist2}).set_index("Val"))
