import netCDF4 as nc
import numpy as np

fn = 'HOLAPS-H-JJA_anomaly-d-2001-2005.nc'
ds = nc.Dataset(fn)

## View metadata:
print(ds)
## Or as a dict:
print(ds.__dict__)

## Print dimensions:
for dim in ds.dimensions.values():
    print(dim)

# output (e.g.):
# <class 'netCDF4._netCDF4.Dimension'> (unlimited): name = 'time', size = 460
# <class 'netCDF4._netCDF4.Dimension'>: name = 'longitude', size = 1233
# <class 'netCDF4._netCDF4.Dimension'>: name = 'latitude', size = 601

# Print variable metadata:
for var in ds.variables.values():
    print(var)

## Return sliced segment of a var array:
## In this case the dims are - time (n=460), latitude (n=601), longitude (n=1233):
heat_flux_array = ds['surface_upward_sensible_heat_flux'][:10,:,:]
# Returns a masked array (this is actually an array with two arrays - one with the data and one with the mask)

# Convert to regular np array with the missing values filled to default val:
heat_flux_array = heat_flux_array.filled(-9999999)

# Save npy array:
np.save('sliced_heat_flux_array_as_toy', heat_flux_array)