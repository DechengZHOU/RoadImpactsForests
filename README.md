# RoadImpactsForests
This repository contains Python code and example data; the full global datasets required to reproduce the study’s key results are publicly available on Figshare (persistent DataCite DOI: https://doi.org/10.6084/m9.figshare.30655661.v1) to reproduce the key analyses in "Global Impacts of Transportation Infrastructure on Forest Degradation and Loss"—a manuscript submitted to Nature Communications for consideration—including:
1.	CalculatingCEI.py: Computes the Comprehensive Environmental Index (CEI) by integrating 13 environmental variables via principal component analysis (PCA).
2.	CalculatingRoadimpact.py: Quantifies road impacts in road/road-reference interface (RRI) zones using the Grid-wise Environmental Matching for Background Reference (GEM-BR) method.

Core Functionality
1. CEI Calculation (CalculatingCEI.py)
This script processes 13 environmental variables spanning climate, soil, and topography:
(1)	Climate: Precipitation (PRE), near-surface air temperature (TAS), incoming shortwave radiation (RSDS), vapor pressure deficit (VPD)
(2)	Soil: Soil depth (DEPTH), sand content (SAND), clay content (CLAY), soil organic carbon (SOC), cation exchange capacity (CEC), pH value (PH)
(3)	Topography: Elevation (DEM), aspect (Aspect), slope (Slope)
PCA is applied to these variables, retaining components with cumulative variance ≥85% to derive objective weights for CEI computation, ensuring the index reflects multi-dimensional environmental conditions.

2. Road Impact Quantification (CalculatingRoadimpact.py)
This script implements the GEM-BR method to estimate road impacts (δI) by:
(1)	Screening reference forest cells using six constraints: spatial proximity to road/RRI zones, CEI similarity (minimizing environmental differences), forest cover change <10% (stable forests), plantation fraction <10% (predominantly natural forests), no nighttime lights (low human disturbance), and ≥3 qualified pixels (statistical robustness).
(2)	Computing reference values (Iref) via inverse distance weighting of qualified reference cells.
(3)	Estimating road impacts:
1)	Absolute impact: δI = Iroad – Iref
2)	Normalized relative impact: δIᵣₑₗ = (Iroad − Iref) / (|Iroad| + |Iref|)

Example Data
A 100 km×100 km test window from South America is provided to validate CEI and δI calculations without full global datasets. All data are formatted as point data (1 km spatial resolution) with a unique pointID for each pixel, enabling conversion back to raster using coordinates (X, Y) in the World Sinusoidal projection (CRS: PROJCS["World_Sinusoidal",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Sinusoidal"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",0.0],UNIT["Meter",1.0],AUTHORITY["ESRI",54008]]).

Input Files
1.	CEI_input.csv
(1)	pointID: Unique identifier for each 1 km pixel
(2)	Climate variables: TAS (°C), PRE (mm/yr), RSDS (W/m²), VPD (hPa)
(3)	Soil variables: DEPTH (cm), SAND (%), CLAY (%), SOC (g/kg), CEC (cmol+/kg), PH (dimensionless)
(4)	Topography variables: DEM (m), Aspect (° from north), Slope (°)
2.	ForestMetrics_input.csv
(1)	pointID, X, Y: Pixel identifier and coordinates
(2)	Buffer_type: Spatial zone classification (1: reference candidate; 2: 4–5 km RRI; 3: 3–4 km RRI; 4: 2–3 km RRI; 5: 1–2 km RRI; 6: 0–1 km road area)
(3)	Forest metrics (2000 and 2020): Area (forest cover, %), H (mean height, m), PD (patch density, patches/km²), NPP (net primary productivity, gC/m²/yr)
(4)	NTL2000/NTL2020: Nighttime lights (digital number, proxy for human activity)
(5)	Windowflag: 1 = pixel in test window (compute road impact); 0 = pixel in 50 km buffer (reference candidate only)
(6)	ForestChange: 2000–2020 forest cover change (% of pixel area; negative = loss, positive = gain)
(7)	Plantations: 2000–2020 plantation fraction (% of pixel area)

Output Files
1.	CEI_output.csv
(1)	pointID: Pixel identifier
(2)	CEI: Comprehensive Environmental Index (dimensionless, 0–1)
2.	ForestMetrics_output.csv
(1)	pointID, X, Y, Buffer_type: Retained from input
(2)	For each metric (Area, H, PD, NPP) in 2000 and 2020:
1)	*_road: Value in road/RRI zone
2)	*_ref: Weighted reference value from GEM-BR
3)	*_AC: Absolute impact 
4)	*_RC: Relative impact
(3)	Temporal trends (2000–2020):
1)	 *_AC_trend (absolute change trend)
2)	*_RC_trend (relative change trend)
(4)	Reference selection metrics: CEI_Diff (CEI difference between road/RRI pixel and references), Nearest_Ref_Distance (km to closest reference), Ref_Points_Used (number of references in calculation)

Implementation Details
(1)	Dependencies: Python 3.12+, with numpy, pandas, rasterio, and scikit-learn.
(2)	Documentation: README.md provides step-by-step run instructions, variable conventions, and validation guidelines using example inputs/outputs.
(3)	Code Standards: All scripts follow PEP 8 guidelines for readability and include inline comments explaining key calculations (e.g., PCA weight derivation, GEM-BR reference screening).
