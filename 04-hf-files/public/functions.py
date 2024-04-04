import ee
import numpy as np

class ImageFunctions:
    def __init__(self) -> None:
        pass

    # Define a function to apply scaling and offset
    def apply_scale_factors(self, image):
        optical_bands = image.select('SR_B.*').multiply(0.0000275).add(-0.2)
        thermal_bands = image.select('ST_B.*').multiply(0.00341802).add(149.0)
        image = image.addBands(optical_bands, None, True)
        image = image.addBands(thermal_bands, None, True)
        return image
    # Define function to return QA bands

    def extract_qa_bits(self, qa_band, start_bit, end_bit, band_name):
        """
        Extracts QA values from an image
        :param qa_band: Single-band image of the QA layer
        :type qa_band: ee.Image
        :param start_bit: Starting bit
        :type start_bit: Integer
        :param end_bit: Ending bit
        :type end_bit: Integer
        :param band_name: New name for the band
        :type band_name: String
        :return: Image with extracted QA values
        :rtype: ee.Image
        """
        # Initialize QA bit string/pattern to check QA band against
        qa_bits = 0
        # Add each specified QA bit flag value/string/pattern to the QA bits to check/extract
        for bit in range(start_bit, end_bit + 1):
            qa_bits += pow(2, bit)  # Same as qa_bits += (1 << bit)
        # Return a single band image of the extracted QA bit values
        return qa_band.select([0], [band_name]).bitwiseAnd(qa_bits).rightShift(start_bit)

    # Define a function to calculate Chlorphyll-a based on trinh et al.(2017)
    def trinh_et_al_chl_a(self, image):
        # extract the cloud and water masks
        qa_band = ee.Image(image).select('QA_PIXEL')
        cloudMask = self.extract_qa_bits(qa_band, 8, 9, "cloud").neq(3)  # different than 3 to remove clouds
        waterMask = self.extract_qa_bits(qa_band, 7, 7, "water").eq(1)  # equals 1 to keep water

        # apply the masks to the image
        image = image.updateMask(cloudMask).updateMask(waterMask)
        image =  self.apply_scale_factors(image)

        a_0 = 0.9375
        a_1 = -1.8862
        blue_bands = image.select('SR_B2')
        green_bands = image.select('SR_B3')
        ln_chl_a = image.expression("a_0 + a_1 * log(blue_bands/green_bands)", {
            'a_0': a_0,
            'a_1': a_1,
            'blue_bands': blue_bands,
            'green_bands': green_bands
        })
        image = image.addBands(ln_chl_a.select([0], ['ln_chl_a']))


        return image

    # Define a function to calculate statistics chl-a

    def extract_data(self, image):
        stats = image.reduceRegion(ee.Reducer.mean(), aoi, 30)
        valid_pixels = image.select('ln_chl_a').unmask().neq(0)  # create a mask of valid pixels
        valid_area = valid_pixels.multiply(ee.Image.pixelArea()).reduceRegion(ee.Reducer.sum(), aoi, 30)  # calculate the area of valid pixels
        return image.set('date', image.date().format()).set(stats).set('Area', valid_area)


    # Define a function to calculate SPM from Novoa et al.(2017) based on Nechad et al. (2010) NIR (recalibrated) model

    def novoa_et_al_spm(self, image):
        # extract the cloud and water masks
        qa_band = ee.Image(image).select('QA_PIXEL')
        cloudMask = self.extract_qa_bits(qa_band, 8, 9, "cloud").neq(3)  # different than 3 to remove clouds
        waterMask = self.extract_qa_bits(qa_band, 7, 7, "water").eq(1)  # equals 1 to keep water

        # apply the masks to the image
        image = image.updateMask(cloudMask).updateMask(waterMask)
        image =  self.apply_scale_factors(image)

    # Select the NIR band (B5 for Landsat 8 OLI)
        nir = image.select('SR_B5')
    # Apply the Nechad et al. (2010) NIR (recalibrated) model
        spm = image.expression(
            "4302 * (nir / (1 - nir / 0.2115))",
            {'nir': nir}
        )
        # Set negative SPM values to zero
        spm = spm.where(spm.lt(0), 0)
        image = image.addBands(spm.select([0], ['spm']))


        return image


    # Define a function to calculate statistics SST

    def extract_data_spm(self, image):
        stats = image.reduceRegion(ee.Reducer.mean(), aoi, 30)
        valid_pixels = image.select('spm').unmask().neq(0)  # create a mask of valid pixels
        valid_area = valid_pixels.multiply(ee.Image.pixelArea()).reduceRegion(ee.Reducer.sum(), aoi, 30)  # calculate the area of valid pixels
        
        return image.set('date', image.date().format()).set(stats).set('Area', valid_area)
    
        # Define a function to calculate SST from Novoa et al.(2017) based on Nechad et al. (2010) NIR (recalibrated) model

    def calculate_sst(self, image):
        # Constants from Table 1
        K1_B10 = 774.8853
        K2_B10 = 1321.0789
        epsilon_B10 = 0.9926
        K1_B11 = 480.8883
        K2_B11 = 1201.1442
        epsilon_B11 = 0.9877

        # extract the cloud and water masks
        qa_band = ee.Image(image).select('QA_PIXEL')
        cloudMask = self.extract_qa_bits(qa_band, 8, 9, "cloud").neq(3)  # different than 3 to remove clouds
        waterMask = self.extract_qa_bits(qa_band, 7, 7, "water").eq(1)  # equals 1 to keep water

        # apply the masks to the image
        image = image.updateMask(cloudMask).updateMask(waterMask)

        # Get the radiance scaling factors for Band 10 from the image's metadata
        ML_B10 = ee.Number(image.get('RADIANCE_MULT_BAND_10'))
        AL_B10 = ee.Number(image.get('RADIANCE_ADD_BAND_10'))
        ML_B11 = ee.Number(image.get('RADIANCE_MULT_BAND_11'))
        AL_B11 = ee.Number(image.get('RADIANCE_ADD_BAND_11'))

        # Get the Band 10 and Band 11 data
        B10 = image.select('B10')
        B11 = image.select('B11')

        # Calculate the at-sensor spectral radiance for Bands 10 and 11
        L_lambda_B10 = B10.multiply(ML_B10).add(AL_B10)
        L_lambda_B11 = B11.multiply(ML_B11).add(AL_B11)

        # Here, you would need to calculate tau, Lu, and Ld using appropriate methods.
        # The formulas you provided do not seem to correspond to standard methods for calculating these quantities.
        # Once you have these, you can calculate SST as follows:

        # Calculate SST using the expression
        SST_B10_Celsius = image.expression(
            "K2_B10 / log(K1_B10 / L_lambda_B10 + 1) - 273.15",
            {
                'K2_B10': K2_B10,
                'K1_B10': K1_B10,
                'L_lambda_B10': L_lambda_B10
            }
        )

        # Add the SST_B10_Celsius band to the image
        image = image.addBands(SST_B10_Celsius.rename('SST_B10_Celsius'))

        return image
    
    def ansari_akhoondzadeh_salinity(self, image):
        # extract the cloud and water masks
        qa_band = ee.Image(image).select('QA_PIXEL')
        cloudMask = self.extract_qa_bits(qa_band, 8, 9, "cloud").neq(3)  # different than 3 to remove clouds
        waterMask = self.extract_qa_bits(qa_band, 7, 7, "water").eq(1)  # equals 1 to keep water

        # apply the masks to the image
        image = image.updateMask(cloudMask).updateMask(waterMask)
        image =  self.apply_scale_factors(image)

        a_0 = 570.80
        a_1 = 26535.17
        a_2 = -62141.71
        a_3 = 34952.89

        coastal_aerosol = image.select('SR_B1')
        blue_bands = image.select('SR_B2')
        green_bands = image.select('SR_B3')
        salinity = image.expression("a_0 + (a_1 *coastal_aerosol) + (a_2 * blue_bands) + (a_3 * green_bands)", {
            'a_0': a_0,
            'a_1': a_1,
            'a_2': a_2,
            'a_3': a_3,
            'coastal_aerosol': coastal_aerosol,
            'blue_bands': blue_bands,
            'green_bands': green_bands
        })

        image = image.addBands(salinity.select([0], ['salinity']))


        return image







  