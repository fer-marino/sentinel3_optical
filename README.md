## Top of  Atmosphere Reflectance
Top of  Atmosphere (TOA) Reflectance  is  a  unitless  number  that  can  be  computed  from satellite spectral radiance,
 the earth-sun distance in astronomical units, the mean solar  exoatmospheric  irradiance  and  the  solar  zenith  angle.

The significance of the TOA reflectance is it represents the solar radiation incident on the instrument in standard unit
 less terms, independent of the position of the sun with respect to the earth. 

When comparing images from different sensors, there are three advantages to using TOA reflectance instead of at-sensor
spectral radiance. First, it removes the cosine effect of different solar zenith angles due to the time difference
between data acquisitions. Second, TOA reflectance compensates for different values of the exoatmospheric solar
irradiance arising from spectral band differences. Third, the TOA reflectance corrects for the variation in the Earth-Sun
distance between different data acquisition dates. 

The TOA reflectance of the Earth is computed according to the equation:

![TOA Formula](http://bit.ly/2ojmQUt)
 \rho_{ \lambda } =  \frac {\pi * L_{\lambda} * d^2}{ESUN_{\lambda} * \ \theta_{\lambda} } 

where
 \rho_{ \lambda } = Planetary TOA reflectance [unitless]
 \pi = Mathematical constant approximately equal to 3.14159 [unitless]
 L_{\lambda} = Spectral radiance at the sensor's aperture [W/(m^2 sr um)]
 d = Earth-Sun distance [astronomical units]
 ESUN_{\lambda} = Mean exoatmospheric solar irradiance [W/(m^2 um)]
 \theta_{\lambda} = solar zenith angle
 
 ### OLCI
 For the OLCI instrument, each radiance band is located in a separated file named OaXX_radiance.nc, containing a variable
 with the same name. Extracting the data is simple using official netcdf library:
 
 ```
 red = open_dataset(product + "/Oa10_radiance.nc")["Oa10_radiance"].values[:]
 green = open_dataset(product + "/Oa05_radiance.nc")["Oa05_radiance"].values[:]
 blue = open_dataset(product + "/Oa03_radiance.nc")["Oa03_radiance"].values[:]
 ```
 
 Here we use xarray library to open each file. Then we access the variable we need via the squadre bracket operator,
 then copy the whole content into a new variable. This basically copy in memory the entire band in a single step, which is
 way more efficient than accessing the single pixels throught this API. Another advantage is that the raw data is store as
 an uint16 insteat of float32, to have smaller products. Then you have to apply a scale factor and a offset to convert it to
 float32, but this is done transparently by the library.
 
 We do the same to ancillary data we need to apply the formula above:
  ```
 instrument_data = open_dataset(product + "/instrument_data.nc")
 tie_geometries = open_dataset(product + "/tie_geometries.nc")

 detector_index = instrument_data["detector_index"].values[:]
 sza = tie_geometries["SZA"].values[:]
 solar_flux = instrument_data["solar_flux"].values[:]
 ```
 
 We are extracting also a variable named `detector_index`. This is a 2D array that for each pixel give us the detector number
 that was used for that pixel, and we need this information to extract the solar flux at each detector.
 
 Finally, we process each pixel applying the formula above. We skip invalid pixels doing a check on the detector_index variable,
 but a similar check could have been done on measurament data.
 ```
 detector = int(detector_index[y][x])
 angle = sza[y][int(x / 64)]
 sol_flux_red = solar_flux[9][detector]  # band 10 for red, has index 9
 sol_flux_green = solar_flux[4][detector]  # band 5 for green, has index 4
 sol_flux_blue = solar_flux[2][detector]  # band 3 for blue, has index 2

 img[y][x][0] = max(0, min(1., math.pi * (red[y][x] / sol_flux_red) / math.cos(math.radians(angle))))*2 -1
 img[y][x][1] = max(0, min(1., math.pi * (green[y][x] / sol_flux_green) / math.cos(math.radians(angle))))*2 -1
 img[y][x][2] = max(0, min(1., math.pi * (blue[y][x] / sol_flux_blue) / math.cos(math.radians(angle))))*2 -1
 ```
 
 The solar zenith angle variable does not fully cover the entire image, it has all the row as the image but for the 
 columns it has one each 64 columns.
 The reflectance is expected to vary from zero to one, anyway this is not always true, expecially on cloud. Anyway we do 
 not care about clouds so we saturate anything above one. We also rescale the value from the range [0, 1] to [-1,1] as
 scipy expect to find those values in float images.
 
 Done? Almost. You can already see the results of this processing, anyway you may notice that for a better results it 
 is necessary to apply some filter to make it looks nicer. The easier way is to apply a histogram equalization filter:
 
 `img_equalized = exposure.equalize_hist(img, nbins=512)`
 
 This filter will adjust the contrast of the image to make it looks nicer. The nbins parameters is the number of bins of 
 the histogram the algorithm will build. Increasing this number will give you more color precision, but it will also make 
 it slower and more greedy on memory during computation.
  
  
  ### SLSTR
  Also for SLSTR we have separate files for each band, here anyway we have also different views to pick the data from.
  The algorithm is almost the same as OLCI with few differences mostly because of the different data structure.
  The only remark is the Sun Zenith angle variable structure: it is a single 2D array which have the nadir view and the
  oblique view placed next to each other, so you need to do some math to place each SZA to the radiance grid. 