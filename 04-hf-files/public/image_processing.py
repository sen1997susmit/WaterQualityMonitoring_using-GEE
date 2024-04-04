import ee
import geemap
import geopandas as gpd
from functions import ImageFunctions
from constants import STUDY_BOUNDARY_PATH, TURBO_PALETTE, VIRIDIS_PALETTE

class ImageProcessor:
    def __init__(self, map_instance):
        self.map_instance = map_instance

    def load_and_process_images(self, processing_function, dates):
        # Load the study area
        print('Loading study boundary')
        study_boundary = gpd.read_file(STUDY_BOUNDARY_PATH)
        ee_boundary = geemap.geopandas_to_ee(study_boundary)
        aoi = ee_boundary.geometry()

        processed_collection = ee.ImageCollection([])

        # Loop through the dates and get the imagery
        for date in dates:
            print(f'Processing image for date {date}')
            start_date = ee.Date(date)
            end_date = start_date.advance(1, 'day')

            # Filter the image collection by date and area
            image = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
                .filterDate(start_date, end_date) \
                .filterBounds(ee_boundary) \
                .first()  # get the first image that matches the filters

            clipped_image = image.clip(aoi)  # Clip the image to the study boundary
            processed_image = processing_function(clipped_image)  # process the image
            processed_collection = processed_collection.merge(processed_image)  # add the image to the processed collection
        print('returning processed collection')
        return processed_collection


       
    
    
    def load_and_process_images_chla(self):
        # Create an instance of ImageFunctions
        image_functions = ImageFunctions()
        processed_collection = self.load_and_process_images(image_functions.trinh_et_al_chl_a, ['2021-11-11', '2021-10-26','2021-10-10', '2021-08-07','2021-07-22', '2021-07-06'])
        return processed_collection
    
    def load_and_process_images_spm(self):
        # Create an instance of ImageFunctions
        image_functions = ImageFunctions()
        processed_collection = self.load_and_process_images(image_functions.novoa_et_al_spm, ['2021-11-11', '2021-10-26','2021-10-10', '2021-08-07','2021-07-22', '2021-07-06'])
        return processed_collection