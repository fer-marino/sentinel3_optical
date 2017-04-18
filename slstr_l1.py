from numpy import float32, zeros, uint16
from scipy.misc import imsave
from skimage import exposure
from time import time
from xarray import open_dataset
import math


def sza_nadir_500(row, col, sza):
    derived_column = int(col / 32)
    return sza[int(min(row / 2, sza.shape[0] - 1))][derived_column]  # TODO add fraction


def process(product):
    # open radiance datasets
    print("Loading data...")
    start_time = time()
    s3_an = open_dataset(product + "/S3_radiance_an.nc")["S3_radiance_an"].values[:]
    s1_an = open_dataset(product + "/S1_radiance_an.nc")["S1_radiance_an"].values[:]
    s5_an = open_dataset(product + "/S5_radiance_an.nc")["S5_radiance_an"].values[:]

    # ancillary data needed for TOA reflectance conversion
    solar_irradiance_s3 = open_dataset(product + "/S3_quality_an.nc")["S3_solar_irradiance_an"].values[:]
    solar_irradiance_s1 = open_dataset(product + "/S1_quality_an.nc")["S1_solar_irradiance_an"].values[:]
    solar_irradiance_s5 = open_dataset(product + "/S5_quality_an.nc")["S5_solar_irradiance_an"].values[:]

    detectors = open_dataset(product + "/indices_an.nc")["detector_an"].values[:]
    sza = open_dataset(product + "/geometry_tn.nc")["solar_zenith_tn"].values[:]

    width = s3_an.shape[1]
    height = s3_an.shape[0]
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
            if not math.isnan(detectors[y][x]) and not math.isnan(s3_an[y][x]) and not math.isnan(s1_an[y][x]) and not math.isnan(s5_an[y][x]):
                sza_corrected = sza_nadir_500(x, y, sza)
                s5_reflectance = max(0, min(1., math.pi * (
                s5_an[y][x] / solar_irradiance_s5[int(detectors[y][x])]) / math.cos(math.radians(sza_corrected))))
                s3_reflectance = max(0, min(1., math.pi * (
                s3_an[y][x] / solar_irradiance_s3[int(detectors[y][x])]) / math.cos(math.radians(sza_corrected))))
                s1_reflectance = max(0, min(1., math.pi * (
                s1_an[y][x] / solar_irradiance_s1[int(detectors[y][x])]) / math.cos(math.radians(sza_corrected))))

                img[y][x][0] = min(1, (s3_reflectance + s5_reflectance) / 2)
                img[y][x][1] = min(1, s3_reflectance)
                img[y][x][2] = min(1, (s3_reflectance + s1_reflectance) / 2)

                img_raw[y][x][0] = (s3_an[y][x] + s5_an[y][x]) / 2
                img_raw[y][x][1] = s3_an[y][x]
                img_raw[y][x][2] = (s3_an[y][x] + s1_an[y][x]) / 2

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
    imsave(product + "/toa_equalized.jpg", img_equalized)
    img_equalized_raw = exposure.equalize_hist(img_raw, nbins=512)
    imsave(product + "/radiance_equalized.jpg", img_equalized_raw)
    print("done in {perf:.2f} seconds ".format(perf=(time() - start_time)))
    img_clahe = exposure.equalize_adapthist(img, nbins=512)
    imsave(product + "/radiance_clahe.jpg", img_clahe)


if __name__ == "__main__":
    product = "C:\\Users\\Fernando\\Downloads\\S3A_SL_1_RBT____20170417T041220_20170417T041520_20170417T060911_0179_016" \
              "_318_2520_SVL_O_NR_002.SEN3"
    process(product)
