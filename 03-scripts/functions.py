# Define a function to apply scaling and offset
def apply_scale_factors(image):
    optical_bands = image.select('SR_B.*').multiply(0.0000275).add(-0.2)
    thermal_bands = image.select('ST_B.*').multiply(0.00341802).add(149.0)
    image = image.addBands(optical_bands, None, True)
    image = image.addBands(thermal_bands, None, True)
    return image

# Define a function to calculate statistics chl-a
def calculate_stats(image, region):
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean().combine(
            reducer2=ee.Reducer.stdDev(),
            sharedInputs=True
        ),
        geometry=region,
        scale=30,  # scale in meters
        maxPixels=1e9
    )
    return stats.getInfo()

# Define function to return QA bands

def extract_qa_bits(qa_band, start_bit, end_bit, band_name):
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
def trinh_et_al_chl_a(image):
    # extract the cloud and water masks
    qa_band = ee.Image(image).select('QA_PIXEL')
    cloudMask = extract_qa_bits(qa_band, 8, 9, "cloud").neq(3)  # different than 3 to remove clouds
    waterMask = extract_qa_bits(qa_band, 7, 7, "water").eq(1)  # equals 1 to keep water

    # apply the masks to the image
    image = image.updateMask(cloudMask).updateMask(waterMask)
    image =  apply_scale_factors(image)

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


def extract_data(image):
    stats = image.reduceRegion(ee.Reducer.mean(), aoi, 30)
    valid_pixels = image.select('ln_chl_a').unmask().neq(0)  # create a mask of valid pixels
    valid_area = valid_pixels.multiply(ee.Image.pixelArea()).reduceRegion(ee.Reducer.sum(), aoi, 30)  # calculate the area of valid pixels
    return image.set('date', image.date().format()).set(stats).set('Area', valid_area)


# Define a function to calculate SPM from Novoa et al.(2017) based on Nechad et al. (2010) NIR (recalibrated) model

def novoa_et_al_spm(image):
    # extract the cloud and water masks
    qa_band = ee.Image(image).select('QA_PIXEL')
    cloudMask = extract_qa_bits(qa_band, 8, 9, "cloud").neq(3)  # different than 3 to remove clouds
    waterMask = extract_qa_bits(qa_band, 7, 7, "water").eq(1)  # equals 1 to keep water

    # apply the masks to the image
    image = image.updateMask(cloudMask).updateMask(waterMask)
    image =  apply_scale_factors(image)

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



def extract_data_spm(image):
    stats = image.reduceRegion(ee.Reducer.mean(), aoi, 30)
    valid_pixels = image.select('spm').unmask().neq(0)  # create a mask of valid pixels
    valid_area = valid_pixels.multiply(ee.Image.pixelArea()).reduceRegion(ee.Reducer.sum(), aoi, 30)  # calculate the area of valid pixels
    return image.set('date', image.date().format()).set(stats).set('Area', valid_area)
