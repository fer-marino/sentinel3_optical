import sys
from netCDF4 import Dataset
import numpy as np
import numpy.ma as ma
import scipy.misc
import math


def process(product):
    # open radiance datasets
    red = Dataset(product + "/Oa10_radiance.nc")
    green = Dataset(product + "/Oa05_radiance.nc")
    blue = Dataset(product + "/Oa03_radiance.nc")

    height = red.dimensions["columns"].size
    width = red.dimensions["rows"].size

    # ancillary data needed for TOA reflectance conversion
    instrument_data = Dataset(product + "/instrument_data.nc")
    tie_geometries = Dataset(product + "/tie_geometries.nc")

    detector_index = instrument_data["detector_index"]
    sza = tie_geometries["SZA"]
    solar_flux = instrument_data["solar_flux"]

    # initialize image
    img = np.zeros((height, width, 3), dtype=np.float32)

    # Set the RGB values
    for y in range(img.shape[0]):
        for x in range(img.shape[1]):
            if detector_index[y][x] is not ma.masked:
                detector = detector_index[y][x]
                angle = sza[y][int(x/64)]
                sol_flux_red = solar_flux[9][detector]
                sol_flux_green = solar_flux[4][detector]
                sol_flux_blue = solar_flux[2][detector]

                img[y][x][0] = math.pi * (red["Oa10_radiance"][y][x] / sol_flux_red) / math.cos(math.radians(angle))
                img[y][x][1] = math.pi * (green["Oa05_radiance"][y][x] / sol_flux_green) / math.cos(math.radians(angle))
                img[y][x][2] = math.pi * (blue["Oa03_radiance"][y][x] / sol_flux_blue) / math.cos(math.radians(angle))

        if (y / width) % 2 == 0:
            print("Processing row ", y, " ", y/width, "%")

    # Display the image
    scipy.misc.imshow(img)

    # Save the image
    scipy.misc.imsave("image.png", img)


if __name__ == "__main__":
    product = "C:\\Users\\Fernando\\Downloads\\S3A_OL_1_EFR____20170415T135038_20170415T135338_20170415T153345_0179_016_295" \
              "_3780_SVL_O_NR_002.SEN3"
    process(product)