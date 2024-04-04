import ee
import geemap
import solara
import os
import sys





# Get the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

module_path = os.path.join(project_root, 'public')
print(module_path)
# Add the module path to the Python path
sys.path.append(module_path)

# Define the path to the shapefile
shapefile_path = os.path.join(project_root,'WaterQuality_SMB', 'public', 'study_boundary.gpkg')





from functions import ImageFunctions
from load_process import ImageProcess
from constants import STUDY_BOUNDARY_PATH



class Map(geemap.Map):
    def __init__(self, selected_image_type, **kwargs):
        print("__init__")
        super().__init__(**kwargs)
        self.functions = ImageProcess(self)
        self.image_functions = ImageFunctions()
        self.add_layer_manager()
        self.selected_image_type = selected_image_type
        self.update_image()

    def update_image(self):
        print("update_image called")
        if self.selected_image_type == "True Color":
            self.functions.load_and_process_true(self, STUDY_BOUNDARY_PATH)
        elif self.selected_image_type == "Chl-a":
            self.functions.load_and_process_chla(self, STUDY_BOUNDARY_PATH)
        elif self.selected_image_type == 'SPM':
            self.functions.load_and_process_spm(self, STUDY_BOUNDARY_PATH)
        elif self.selected_image_type == 'SST':
            self.functions.load_and_process_sst(self, STUDY_BOUNDARY_PATH)
        elif self.selected_image_type == 'Salinity':
            self.functions.load_and_process_salinity(self, STUDY_BOUNDARY_PATH)

    def set_selected_image_type(self, new_image_type):
        self.selected_image_type = new_image_type
        self.update_image()




@solara.component
def Page():
    selected_image_type, set_selected_image_type = solara.use_state_or_update("True Color")

    def on_change_callback(new_value):
        print(new_value)
        set_selected_image_type(new_value)

    with solara.Column(style={"min-width": "500px"}):
        with solara.Card(title="Water Quality Monitoring in Santa Monica Bay", subtitle="Using Landsat 8 OLI Satellite Data"):
            solara.Markdown(
'''        
## Overview

This Earth Engine application focuses on monitoring water quality in the Santa Monica Bay using Landsat 8 OLI satellite data. The primary objective is to analyze Chlorophyll-a concentrations, which serve as a key indicator of water quality.

## Background

This project is an extension of the original 2015 research by Trinh et al., which focused on the capabilities of Landsat 8 OLI and Aqua MODIS to monitor water quality in the Santa Monica Bay (SMB). The research was centered on the impact of the Hyperion Treatment Plant (HTP), which discharges treated wastewater into the bay, increasing contaminant and nitrogen concentrations and the likelihood of phytoplankton blooms. The original project is available [here](https://romero61.github.io/posts/SMB/).

## Analysis

The extension applies the findings of Trinh et al. to the July 11th, 2021, HTP failure, where 17 million gallons of untreated sewage were released 1-mile offshore. Reports indicate that the plant was operating at a diminished capacity several months after the initial failure. The local OLI algorithm, developed in the original research, was used to measure the chlorophyll-a concentration in response to the 2021 HTP failure.

## Significance

Monitoring water quality is crucial for the preservation of marine ecosystems. Changes in Chlorophyll-a concentrations can indicate the presence of harmful algal blooms, which can have detrimental effects on marine life. This application provides a valuable tool for ongoing monitoring and research efforts. The results indicated possible effects of the untreated wastewater discharge on the SMB's water quality, although further studies are needed for a more in-depth analysis.

# Current Development 

1. CURRENT BUG: App Requires switching back to TRUE COLOR then choosing SPM, Chl-a or SST.
2. Need to update with 'In progress' spinner to indicate that selection is currently running.
3. Not Visible but inital start up of the app runs rendering of the map several times slowing down start up
4. New page should load with a split map of Chl-a & SPM for most recent date
5. User should be able to select date from calendar (considering a range of dates but this will slow down app will require testing).
6. I want to extend the draw feature functionality of ipyleaflet so that stats are created for the user defined region.
7. Need to build in returning dataframe to build plots. 

'''
            )

        with solara.Column(style={'min-width': "500px"}):
            with solara.Card(title = 'Select Map Type', subtitle = 'Choose between True Color, Chlorophyll-a, Suspended Particle Matter, Sea Surface Temperature'):
                solara.ToggleButtonsSingle(value=selected_image_type, values=["True Color", "Chl-a", "SPM", "SST", 'Salinity'], on_value=on_change_callback)
                solara.Markdown('''Currently bugged between switching: Return to TRUE COLOR then switch to CHL-A, SPM, or SST''')
                Map(selected_image_type).element(
                    selected_image_type= selected_image_type,
                    center=[33.901, -118.477],
                    zoom=12,
                    height="800px"
                )
        
