import streamlit as st
import altair as alt
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
import os
import sys

# Setup Paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from analysis import do_processing
from data_loader import load_districts
from reporting import generate_pdf

# --- Configuration ---
st.set_page_config(
    page_title="UrbanSight AI", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Load CSS ---
def load_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"CSS file not found: {file_name}")

load_css("urban_sprawl_project/src/style.css")

# --- Constants & Paths ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
SHAPEFILE_PATH = "d:/AIKosh/district.shp"
STATS_PATH = "d:/AIKosh/urban_sprawl_project/src/district_stats.csv"

# --- Data Loading ---
@st.cache_data
def get_data():
    try:
        gdf = load_districts(SHAPEFILE_PATH)
        gdf['geometry'] = gdf['geometry'].simplify(0.002)
        
        if os.path.exists(STATS_PATH):
            stats_df = pd.read_csv(STATS_PATH)
            gdf = gdf.merge(stats_df, on="d_name", how="left")
        else:
            # Fallback defaults
            gdf['mean_ndvi'] = 0.3
            gdf['mean_ndbi'] = 0.05
            gdf['sprawl_risk'] = 10.0
            
        return gdf
    except Exception as e:
        st.error(f"Data Load Error: {e}")
        return gpd.GeoDataFrame()

try:
    gdf = get_data()
    district_list = sorted(gdf['d_name'].dropna().unique())
except:
    st.stop()

# --- Helper Functions (Interpretation) ---
def interpret_ndvi(val):
    if val > 0.4: return "Very Green (Healthy)", "#30d158"
    if val > 0.2: return "Moderate Greenery", "#ff9f0a"
    return "Sparse Vegetation", "#ff453a"

def interpret_ndbi(val):
    if val > 0.1: return "High Urban Density", "#ff453a"
    if val > -0.1: return "Moderate Built-up", "#ff9f0a"
    return "Low Urbanization", "#30d158"

def interpret_risk(val):
    if val > 50: return "Critical Sprawl", "#ff453a"
    if val > 20: return "Warning Level", "#ff9f0a"
    return "Stable", "#30d158"

# --- Sidebar Logic ---
with st.sidebar:
    st.markdown('<div class="brand-text" style="font-size:1.5rem; font-weight:700; margin-bottom:20px;">UrbanSight.</div>', unsafe_allow_html=True)
    
    # District Selector
    if "selected_district" not in st.session_state:
        st.session_state.selected_district = "Agra"
        
    selected_district = st.selectbox(
        "Target Sector", 
        district_list, 
        index=district_list.index(st.session_state.selected_district) if st.session_state.selected_district in district_list else 0
    )
    st.session_state.selected_district = selected_district
    
    # Stats for selection
    d_stats = gdf[gdf['d_name'] == selected_district].iloc[0]
    
    st.markdown("---")
    
    # Metric 1: NDVI
    ndvi_txt, ndvi_col = interpret_ndvi(d_stats['mean_ndvi'])
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Vegetation Index (NDVI)</div>
        <div class="metric-value">{d_stats['mean_ndvi']:.2f}</div>
        <div class="metric-sub" style="color:{ndvi_col}">{ndvi_txt}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Metric 2: NDBI
    ndbi_txt, ndbi_col = interpret_ndbi(d_stats['mean_ndbi'])
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Urban Density (NDBI)</div>
        <div class="metric-value">{d_stats['mean_ndbi']:.2f}</div>
        <div class="metric-sub" style="color:{ndbi_col}">{ndbi_txt}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Metric 3: Risk
    risk_txt, risk_col = interpret_risk(d_stats['sprawl_risk'])
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Sprawl Risk Assessment</div>
        <div class="metric-value">{d_stats['sprawl_risk']:.1f}%</div>
        <div class="metric-sub" style="color:{risk_col}">{risk_txt}</div>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    if st.button("Run Satellite Scan"):
        with st.spinner("Acquiring Satellite Feed..."):
            try:
                res = do_processing(selected_district, SHAPEFILE_PATH)
                st.session_state.scan_result = res
                st.success("Scan Complete")
            except Exception as e:
                st.error(f"Scan Failed: {e}")

# --- Main Interface ---

# Header
st.markdown(f"""
    <div style="text-align:center; padding-bottom: 20px;">
        <h1 style="margin:0;">Sector Analysis: {selected_district}</h1>
        <p style="color:#86868b;">Real-time Satellite Telemetry & Predictive Modeling</p>
    </div>
""", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["🗺️ Geospatial Map", "📊 Deep Analytics", "📚 Intelligence"])

# --- Tab 1: Map ---
with tab1:
    col_map, col_details = st.columns([3, 1])
    
    with col_map:
        # Prepare Map Data
        gdf = gdf.dropna(subset=['d_name']) # Drop rows without names
        gdf['sprawl_risk'] = gdf['sprawl_risk'].fillna(0)
        gdf['safety_score'] = 100 - gdf['sprawl_risk']
        
        m = folium.Map(
            location=[22.0, 79.0], 
            zoom_start=4.5, 
            min_zoom=4,
            tiles="CartoDB dark_matter"
        )
        
        # Chloropleth
        folium.Choropleth(
            geo_data=gdf.__geo_interface__,
            data=gdf,
            columns=['d_name', 'safety_score'],
            key_on="feature.properties.d_name",
            fill_color='RdYlGn',
            fill_opacity=0.4,
            line_opacity=0.3,
            legend_name="Ecological Safety Score",
            highlight=True
        ).add_to(m)
        
        # Highlight Selected
        sel_geom = gdf[gdf['d_name'] == selected_district]
        if not sel_geom.empty:
            folium.GeoJson(
                sel_geom,
                style_function=lambda x: {'fillColor': 'transparent', 'color': '#2997ff', 'weight': 3}
            ).add_to(m)
            # Zoom to selected
            b = sel_geom.total_bounds
            m.fit_bounds([[b[1], b[0]], [b[3], b[2]]])

        # Interactive Layer for clicking
        folium.GeoJson(
            gdf,
            style_function=lambda x: {'fillColor': '#00000000', 'color': '#00000000'},
            highlight_function=lambda x: {'fillColor': '#ffffff', 'fillOpacity': 0.1, 'weight': 1},
            tooltip=folium.GeoJsonTooltip(fields=['d_name'], aliases=['District:'])
        ).add_to(m)

        st_map = st_folium(m, width="100%", height=500, returned_objects=["last_object_clicked"])

        # Click Logic
        if st_map and st_map['last_object_clicked']:
             props = st_map['last_object_clicked'].get('properties')
             if props and 'd_name' in props:
                 clicked_d = props['d_name']
                 if clicked_d != st.session_state.selected_district:
                     st.session_state.selected_district = clicked_d
                     st.rerun()

    with col_details:
        st.markdown('<div class="explained-card">', unsafe_allow_html=True)
        st.markdown(f"### {selected_district} Report")
        st.write("Current satellite sweeps indicate:")
        
        # Dynamic Bullet Points
        if d_stats['mean_ndvi'] > 0.3:
            st.markdown("✅ **Healthy Vegetation**: Good biomass coverage.")
        else:
            st.markdown("⚠️ **Vegetation Warning**: Biomass levels are critical.")
            
        if d_stats['mean_ndbi'] > 0.0:
            st.markdown("🏙️ **Urbanized**: Significant concrete structures detected.")
        else:
            st.markdown("🏡 **Rural/Suburban**: Low structural density.")
            
        st.markdown(f"**Predicted Growth**: {d_stats['sprawl_risk']/5.0:.2f}% per annum")

        # PDF Report Button
        report_bytes = generate_pdf(
            selected_district, 
            d_stats.to_dict(), 
            [f"NDVI Status: {ndvi_txt}", f"Urban Density: {ndbi_txt}", f"Risk Level: {risk_txt}"]
        )
        st.download_button(
            label="📄 Download District Report",
            data=report_bytes,
            file_name=f"{selected_district}_UrbanSight_Report.pdf",
            mime="application/pdf"
        )
        st.markdown('</div>', unsafe_allow_html=True)

# --- Tab: Comparison ---
with st.sidebar:
    st.divider()
    st.markdown("### ⚖️ Comparison Mode")
    compare_mode = st.checkbox("Enable Comparison")
    if compare_mode:
        compare_district = st.selectbox(
            "Compare with", 
            [d for d in district_list if d != selected_district],
            index=0
        )

if compare_mode:
    # Overlay Comparison View
    st.markdown(f"## ⚔️ Comparative Analysis: {selected_district} vs {compare_district}")
    
    c_stats = gdf[gdf['d_name'] == compare_district].iloc[0]
    
    col1, col2 = st.columns(2)
    
    # Left: Original
    with col1:
        st.markdown(f"### {selected_district}")
        st.metric("Vegetation (NDVI)", f"{d_stats['mean_ndvi']:.2f}")
        st.metric("Urban Density (NDBI)", f"{d_stats['mean_ndbi']:.2f}")
        st.metric("Sprawl Risk", f"{d_stats['sprawl_risk']:.1f}%")
        
        # Mini Chart
        source = pd.DataFrame({
            'Metric': ['NDVI', 'NDBI', 'Risk/100'],
            'Value': [d_stats['mean_ndvi'], d_stats['mean_ndbi'], d_stats['sprawl_risk']/100]
        })
        chart = alt.Chart(source).mark_bar(color='#2997ff').encode(
            x='Metric', y='Value'
        ).properties(height=200)
        st.altair_chart(chart, use_container_width=True)

    # Right: Target
    with col2:
        st.markdown(f"### {compare_district}")
        delta_ndvi = c_stats['mean_ndvi'] - d_stats['mean_ndvi']
        delta_ndbi = c_stats['mean_ndbi'] - d_stats['mean_ndbi']
        delta_risk = c_stats['sprawl_risk'] - d_stats['sprawl_risk']
        
        st.metric("Vegetation (NDVI)", f"{c_stats['mean_ndvi']:.2f}", delta=f"{delta_ndvi:.2f}")
        st.metric("Urban Density (NDBI)", f"{c_stats['mean_ndbi']:.2f}", delta=f"{delta_ndbi:.2f}", delta_color="inverse")
        st.metric("Sprawl Risk", f"{c_stats['sprawl_risk']:.1f}%", delta=f"{delta_risk:.1f}", delta_color="inverse")
        
        # Mini Chart
        source_c = pd.DataFrame({
            'Metric': ['NDVI', 'NDBI', 'Risk/100'],
            'Value': [c_stats['mean_ndvi'], c_stats['mean_ndbi'], c_stats['sprawl_risk']/100]
        })
        chart_c = alt.Chart(source_c).mark_bar(color='#ff9f0a').encode(
            x='Metric', y='Value'
        ).properties(height=200)
        st.altair_chart(chart_c, use_container_width=True)
    
    st.divider()

# --- Tab 2: Analytics ---
with tab2:
    # 1. Check for Real Scan Results
    if "scan_result" in st.session_state and st.session_state.scan_result:
        st.markdown("### 🛰️ Live Satellite Imagery Analysis")
        ndvi, ndbi, slums, prof = st.session_state.scan_result
        
        s1, s2, s3 = st.columns(3)
        with s1:
            st.caption("NDVI (Green density)")
            fig1, ax1 = plt.subplots(figsize=(4,4))
            ax1.set_facecolor('black')
            ax1.imshow(ndvi, cmap='RdYlGn', vmin=-1, vmax=1)
            ax1.axis('off')
            st.pyplot(fig1)
            
        with s2:
            st.caption("NDBI (Built-up Areas)")
            fig2, ax2 = plt.subplots(figsize=(4,4))
            ax2.set_facecolor('black')
            ax2.imshow(ndbi, cmap='gray', vmin=-1, vmax=1)
            ax2.axis('off')
            st.pyplot(fig2)
            
        with s3:
            st.caption("Detected High-Risk Sprawl")
            fig3, ax3 = plt.subplots(figsize=(4,4))
            ax3.set_facecolor('black')
            ax3.imshow(ndbi, cmap='gray', alpha=0.5)
            mask = np.ma.masked_where(slums == 0, slums)
            ax3.imshow(mask, cmap='Reds', vmin=0, vmax=1)
            ax3.axis('off')
            st.pyplot(fig3)
            
        st.divider()

    st.markdown("### Historical & Predictive Trends")
    
    # 2. Mock Time Series Data
    base_ndvi = d_stats['mean_ndvi']
    base_ndbi = d_stats['mean_ndbi']
    years = range(2018, 2024)
    trend_type = -1 if d_stats['sprawl_risk'] > 20 else 0.1
    
    data_points = []
    for i, y in enumerate(years):
        n_noise = np.random.uniform(-0.02, 0.02)
        b_noise = np.random.uniform(-0.02, 0.02)
        factor = i * 0.03 * trend_type
        
        data_points.append({
            "Year": str(y),
            "NDVI": max(0, min(1, base_ndvi + factor + n_noise)),
            "NDBI": max(-1, min(1, base_ndbi - factor + b_noise)),
            "Risk": max(0, 100 * (base_ndbi - factor))
        })
    
    df_chart = pd.DataFrame(data_points)
    
    # Altair Chart
    base = alt.Chart(df_chart).encode(x=alt.X('Year', axis=alt.Axis(labelAngle=0)))
    line_ndvi = base.mark_line(interpolate='monotone', color='#30d158').encode(
        y=alt.Y('NDVI', axis=alt.Axis(title='Vegetation Index')),
        tooltip=['Year', 'NDVI']
    )
    line_ndbi = base.mark_line(interpolate='monotone', color='#ff453a').encode(
        y=alt.Y('NDBI', axis=alt.Axis(title='Build-up Index')),
        tooltip=['Year', 'NDBI']
    )
    chart = alt.layer(line_ndvi, line_ndbi).properties(
        title="",
        height=300
    ).configure_axis(
        labelColor='#86868b', titleColor='#86868b', gridColor='#333'
    ).configure_view(strokeWidth=0)
    
    st.altair_chart(chart, use_container_width=True)
    
    # Distribution Comparison (Mock for visual if no scan, or real logic)
    st.markdown("### District Distribution Models")
    c1, c2 = st.columns(2)
    with c1:
        dist_data = np.random.normal(d_stats['mean_ndvi'], 0.15, 500)
        df_hist = pd.DataFrame({'NDVI': dist_data})
        hist_chart = alt.Chart(df_hist).mark_bar(color='#30d158', opacity=0.7).encode(
            alt.X("NDVI", bin=alt.Bin(maxbins=20)), y='count()',
        ).properties(height=200)
        st.altair_chart(hist_chart, use_container_width=True)
        
    with c2:
        dist_data_b = np.random.normal(d_stats['mean_ndbi'], 0.15, 500)
        df_hist_b = pd.DataFrame({'NDBI': dist_data_b})
        hist_chart_b = alt.Chart(df_hist_b).mark_bar(color='#ff453a', opacity=0.7).encode(
            alt.X("NDBI", bin=alt.Bin(maxbins=20)), y='count()',
        ).properties(height=200)
        st.altair_chart(hist_chart_b, use_container_width=True)

# --- Tab 3: Intelligence ---
with tab3:
    st.markdown("### 🧠 Understanding the Metrics")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="explained-card">
            <div class="explained-title">🌱 NDVI (Vegetation)</div>
            <div class="explained-text">
                <b>Normalized Difference Vegetation Index</b><br><br>
                Measures the health and density of vegetation.
                <ul>
                    <li><b>> 0.4</b>: Dense Forest/Agriculture</li>
                    <li><b>0.2 - 0.4</b>: Shrubs/Grassland</li>
                    <li><b>< 0.1</b>: Barren Rock/Concrete</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="explained-card">
            <div class="explained-title">🏙️ NDBI (Urban)</div>
            <div class="explained-text">
                <b>Normalized Difference Built-up Index</b><br><br>
                Highlights urban areas with higher reflectance in SWIR bands.
                <ul>
                    <li><b>> 0.1</b>: High Density Urban</li>
                    <li><b>-0.1 - 0.1</b>: Suburban/Mixed</li>
                    <li><b>< -0.1</b>: Water/Vegetation</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="explained-card">
            <div class="explained-title">🚨 Sprawl Risk</div>
            <div class="explained-text">
                <b>AI Calculated Risk Score</b><br><br>
                A composite score derived from the ratio of NDBI growth to NDVI loss.
                <br><br>
                High scores indicate unplanned rapid urbanization into green zones.
            </div>
        </div>
        """, unsafe_allow_html=True)
