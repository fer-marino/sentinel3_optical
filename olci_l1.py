from numpy import float32, zeros, uint16
from scipy.misc import imsave
from skimage import exposure
from time import time
from xarray import open_dataset
import math


def process(product):
    # open radiance datasets
    print("Loading data...")
    start_time = time()
    red = open_dataset(product + "/Oa10_radiance.nc")["Oa10_radiance"].values[:]
    green = open_dataset(product + "/Oa05_radiance.nc")["Oa05_radiance"].values[:]
    blue = open_dataset(product + "/Oa03_radiance.nc")["Oa03_radiance"].values[:]

    # ancillary data needed for TOA reflectance conversion
    instrument_data = open_dataset(product + "/instrument_data.nc")
    tie_geometries = open_dataset(product + "/tie_geometries.nc")

    detector_index = instrument_data["detector_index"].values[:]
    sza = tie_geometries["SZA"].values[:]
    solar_flux = instrument_data["solar_flux"].values[:]

    width = instrument_data["detector_index"].sizes["columns"]
    height = instrument_data["detector_index"].sizes["rows"]
    print("Loading completed in {w:.2f} seconds".format(w=time() - start_time))

    # initialize image
    img = zeros((height, width, 3), dtype=float32)
    img_raw = zeros((height, width, 3), dtype=uint16)

    # Set the RGB values
    print("Processing started. Dimension w:{w:d} h:{h:d}".format(w=width, h=height))
    start_time = time()
    perf_time = time()
    counter = 0
    for y in range(img.shape[0]):
        for x in range(img.shape[1]):
            counter += 1
            if not math.isnan(detector_index[y][x]):
                detector = int(detector_index[y][x])
                angle = sza[y][int(x / 64)]
                sol_flux_red = solar_flux[9][detector]  # band 10 for red, has index 9
                sol_flux_green = solar_flux[4][detector]  # band 5 for green, has index 4
                sol_flux_blue = solar_flux[2][detector]  # band 3 for blue, has index 2

                img[y][x][0] = max(0, min(1., math.pi * (red[y][x] / sol_flux_red) / math.cos(math.radians(angle))))
                img[y][x][1] = max(0, min(1., math.pi * (green[y][x] / sol_flux_green) / math.cos(math.radians(angle))))
                img[y][x][2] = max(0, min(1., math.pi * (blue[y][x] / sol_flux_blue) / math.cos(math.radians(angle))))

                img_raw[y][x][0] = red[y][x]
                img_raw[y][x][1] = green[y][x]
                img_raw[y][x][2] = blue[y][x]

        if time() - perf_time > 30:
            print(" * * Processing row {row:d} {perc:.3f}% - Pixel per seconds: {perf:d}".format(row=y, perc=(
                                                                                                             y / height) * 100,
                                                                                                 perf=int(counter / (
                                                                                                 time() - perf_time))))
            counter = 0
            perf_time = time()

    print("Processing finished in {perf:.2f} seconds ".format(perf=(time() - start_time)))

    print("Saving raw...")
    imsave(product + "/toa_reflectance.jpg", img)
    # adjust contrast
    print("Equalizing...")
    start_time = time()
    img_equalized = exposure.equalize_hist(img, nbins=512)
    img_equalized_raw = exposure.equalize_hist(img_raw, nbins=512)

    # Save the image
    imsave(product + "/toa_reflectance_equalized.jpg", img_equalized)
    imsave(product + "/radiance_equalized.jpg", img_equalized_raw)
    print("done in {perf:.2f} seconds ".format(perf=(time() - start_time)))

    img_clahe = exposure.equalize_adapthist(img, nbins=512)
    imsave(product + "/radiance_clahe.jpg", img_clahe)


if __name__ == "__main__":
    product = "C:\\Users\\Fernando\\Downloads\\S3A_OL_1_EFR____20170415T135038_20170415T135338_20170415T153345_0179_016_295" \
              "_3780_SVL_O_NR_002.SEN3"
    process(product)
