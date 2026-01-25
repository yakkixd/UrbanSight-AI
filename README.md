# UrbanSight Project

**Monitoring Urban Sprawl and Slums in India**

UrbanSight AI is a geospatial analysis tool designed to monitor urban sprawl and assess urban health using satellite data indices like NDVI (Normalized Difference Vegetation Index) and NDBI (Normalized Difference Built-up Index).

## Features
- **Interactive Map**: Visualize district-level safety and risk scores.
- **Growth Prediction**: Simple projection of urban sprawl over time.
- **Analysis**: Detailed breakdown of green cover vs. urban build-up.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd urban_sprawl_project
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the Streamlit application:
   ```bash
   streamlit run src/app.py
   ```

2. The application will open in your default browser.

> **Note**: This project requires a shapefile for district boundaries (`district.shp`). Ensure this file is available and the path is correctly configured in `src/app.py`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
