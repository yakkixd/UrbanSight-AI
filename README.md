# 🏙️ UrbanSight AI

### Monitoring Urban Sprawl & Environmental Health in India

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-success)

**UrbanSight AI** is a geospatial analytics platform designed to monitor urbanization trends, assess vegetation loss, and identify potential high-risk sprawl areas across Indian districts. By leveraging satellite imagery (Sentinel-2) and spectral indices (NDVI, NDBI), it provides actionable insights for urban planners and researchers.

---

## 🌟 Key Features

### 1. 🗺️ Interactive Dashboard
- **District-Level Insights**: Explore a dynamic map of India with district-wise analysis.
- **Risk Assessment**: Visual "Safety Scores" and "Sprawl Risk" heatmaps powered by geospatial data.
- **Drill-Down Capability**: Click on any district (e.g., *Agra*, *Bangalore*) to view localized stats.

### 2. 🛰️ Spectral Analysis
- **NDVI (Green Cover)**: Quantifies vegetation density to monitor deforestation and green spaces.
- **NDBI (Urban Build-up)**: Detects concrete structures and urban density.
- **Slum & Sprawl Detection**: Identifies areas with high build-up and low vegetation, indicating unplanned growth.

### 3. 📈 Predictive Modeling
- **Growth Projections**: Simulates urban expansion scenarios over the next 5 years based on current sprawl risk rates.
- **Historic Trends**: (Planned) Analysis of historical changes to predict future patterns.

---

## 📂 Dataset Source

The core geospatial boundaries for this project are sourced from the **IndiaAI Datasets** portal.

- **Dataset Name**: 2011 Population Census District Polygon Geometries
- **Source**: [IndiaAI - AIKosh](https://aikosh.indiaai.gov.in/home/datasets/details/2011_population_census_district_polygon_geometries.html)
- **Description**: Polygon geometries for Indian districts based on the 2011 Census.

> **⚠️ Data Setup Required**: 
> Due to file size limits, the shapefiles are not stored in this repository. 
> 1. Download the shapefile from the link above.
> 2. Extract the files (`.shp`, `.shx`, `.dbf`, etc.).
> 3. Place them in the `urban_sprawl_project/data/` directory.
> 4. Rename the main file to `district.shp` (or ensure the code points to your filename).

---

## 🛠️ Tech Stack

- **Core**: Python 3.9+
- **Geospatial**: `geopandas`, `rasterio`, `shapely`, `folium`
- **Satellite Data**: `pystac-client`, `planetary-computer` (Microsoft)
- **Visualization**: `streamlit`, `matplotlib`, `streamlit-folium`
- **Data Processing**: `pandas`, `numpy`, `scipy`

---

## 🚀 Installation & Setup

### Prerequisites
- Python installed (recommended: 3.9 or higher).
- A [Microsoft Planetary Computer](https://planetarycomputer.microsoft.com/) account (optional, for fetching live Sentinel data).

### Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yakkixd/UrbanSight-AI.git
   cd urban_sprawl_project
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare Data**
   Ensure your `data/` directory looks like this:
   ```
   urban_sprawl_project/
   ├── data/
   │   ├── district.shp  <-- REQUIRED
   │   ├── district.shx
   │   ├── district.dbf
   │   └── ...
   ```

4. **Run the App**
   ```bash
   streamlit run src/app.py
   ```

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).

---

*Built with ❤️ for Urban Sustainability.*
