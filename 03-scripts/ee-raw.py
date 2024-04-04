# %%
#1) Import all necessary packages
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
import ee
import geemap.foliumap as geemap
import geopandas as gpd
import ipywidgets as widgets
import ipyleaflet


# %%
from constants import   STUDY_BOUNDARY_PATH


# %% [markdown]
# # Import Landsat8 OLI
# 
# https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1_L2#terms-of-use
# 
#  Landsat-8 image courtesy of the U.S. Geological Survey

# %%
#ee.Authenticate()
ee.Initialize()

# %%
# Create an interactive map
Map = geemap.Map()
Map.add_basemap(basemap='SATELLITE')



# %%
# Define the collection
collection = "LANDSAT/LC08/C02/T1_L2"

# %%
shapefile_path = STUDY_BOUNDARY_PATH
study_boundary = gpd.read_file(shapefile_path)

# %%
# Load the study area
ee_boundary = geemap.geopandas_to_ee(study_boundary)


# %%
aoi = ee_boundary.geometry()

# %%
# Define the dates of interest
dates = ['2021-07-06', '2021-07-22', '2021-08-07', '2021-10-10', '2021-10-26', '2021-11-11']


# %%
def apply_scale_factors(image):
    optical_bands = image.select('SR_B.*').multiply(0.0000275).add(-0.2)
    thermal_bands = image.select('ST_B.*').multiply(0.00341802).add(149.0)
    image = image.addBands(optical_bands, None, True)
    image = image.addBands(thermal_bands, None, True)
    return image


# %%
vis_params = { "bands": ['SR_B4', 'SR_B3', 'SR_B2'],
  "min": 0.0,
  "max": 0.3
}

# %%
# Loop through the dates and get the imagery
for date in dates:
    start_date = ee.Date(date)
    end_date = start_date.advance(1, 'day')

    # Filter the image collection by date and area
    image = ee.ImageCollection(collection) \
        .filterDate(start_date, end_date) \
        .filterBounds(aoi) \
        .first()  # get the first image that matches the filters

    if image:  # check if image exists
        print(f"Image for date {date} found!")
        processed_image = apply_scale_factors(image)
        Map.addLayer(processed_image, vis_params, date)  # add the image to the map
    else:
        print(f"No image found for date {date}")

# Set the map to focus on the study area
Map.centerObject(ee_boundary, zoom=10)
# Display the map
Map



