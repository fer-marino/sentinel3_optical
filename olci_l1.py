from numpy import float32, zeros
import scipy.misc as im
import math
from skimage import exposure
import time
import xarray as xr

def process(product):
    # open radiance datasets
    red = xr.open_dataset(product + "/Oa10_radiance.nc")["Oa10_radiance"]
    green = xr.open_dataset(product + "/Oa05_radiance.nc")["Oa05_radiance"]
    blue = xr.open_dataset(product + "/Oa03_radiance.nc")["Oa03_radiance"]

    width = red.sizes["columns"]
    height = red.sizes["rows"]

    # ancillary data needed for TOA reflectance conversion
    instrument_data = xr.open_dataset(product + "/instrument_data.nc")
    tie_geometries = xr.open_dataset(product + "/tie_geometries.nc")

    detector_index = instrument_data["detector_index"]
    sza = tie_geometries["SZA"]
    solar_flux = instrument_data["solar_flux"]

    # initialize image
    img = zeros((height, width, 3), dtype=float32)
    img_raw = zeros((height, width, 3), dtype=float32)

    # Set the RGB values
    print("Processing started. Dimension w:{w:d} h:{h:d}".format(w=width, h=height))
    start_time = time.time()
    counter = 0
    for y in range(img.shape[0]):
        for x in range(img.shape[1]):
            counter += 1
            if not math.isnan(detector_index.values[y][x]):
                detector = int(detector_index.values[y][x])
                angle = sza.values[y][int(x/64)]
                sol_flux_red = solar_flux.values[9][detector]
                sol_flux_green = solar_flux.values[4][detector]
                sol_flux_blue = solar_flux.values[2][detector]

                img[y][x][0] = math.pi * (red.values[y][x] / sol_flux_red) / math.cos(math.radians(angle))
                img[y][x][1] = math.pi * (green.values[y][x] / sol_flux_green) / math.cos(math.radians(angle))
                img[y][x][2] = math.pi * (blue.values[y][x] / sol_flux_blue) / math.cos(math.radians(angle))

                img_raw[y][x][0] = red.values[y][x]
                img_raw[y][x][1] = green.values[y][x]
                img_raw[y][x][2] = blue.values[y][x]

        if time.time() - start_time > 30:
            print("Processing row {row:d} {perc:.3f}% - Pixel per seconds: {perf:d}".format(row=y, perc=(y/height)*100, perf=int(counter / (time.time() - start_time))))
            counter = 0
            start_time = time.time()

    print("Processing finished")
    # Display the image
    # im.imshow(img)
    im.imsave(product+".png", img)
    im.imsave(product+"_raw.png", img)
    # adjust contrast
    img_equalized = exposure.equalize_hist(img, nbins=1024)
    img_equalized_raw = exposure.equalize_hist(img_raw, nbins=1024)
    # im.imshow(img_equalized)

    # Save the image
    im.imsave(product+"_equalized.png", img_equalized)
    im.imsave(product+"_equalized_raw.png", img_equalized_raw)


if __name__ == "__main__":
    product = "C:\\Users\\Fernando\\Downloads\\S3A_OL_1_EFR____20170415T135038_20170415T135338_20170415T153345_0179_016_295" \
              "_3780_SVL_O_NR_002.SEN3"
    process(product)