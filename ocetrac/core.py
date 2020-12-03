# AUTOGENERATED! DO NOT EDIT! File to edit: 00_core.ipynb (unless otherwise specified).

__all__ = ['label_2D', 'track_3D', 'mhw']

# Cell
def label_2D(da, fieldname):
    '''2D image labeling'''

    # pick a data variable
    data = _check_input(da, fieldname)

    # Converts data to binary, defines structuring element, and performs morphological closing then opening
    mo_binary = _morphological_operations(data, include_poles=False, radius=8)

    # label 2D features from binary images
    id_2D = _id(binary_images)

    # wrap labels that cross prime meridian
    bitmap_binary_2E, bitmap_bool_2E = _wrap_labels(id_2D)

    ### ! Reapply land maks HERE

    # relabel 2D features from binary images that are wrapped around meridian
    id_2D_wrap = _id(bitmap_binary_2E)

    # Convert labels to DataArray
    id_2D_wrap = xr.DataArray(id_2D_wrap,
                              dims=bitmap_bool_2E.dims,
                              coords=bitmap_bool_2E.coords)
    id_2D_wrap = id_2D_wrap.where(id_2D_wrap!= 0, drop=False, other=np.nan)

    # calculatre area with regionprops
    area, min_area, labelprops = _id_area(id_2D_wrap, .75)

    keep_labels = labelprops.where(area>=min_area, drop=True)

    id_2D_area_bool = xr.DataArray(np.in1d(id_2D_wrap, keeplabels).reshape(id_2D_wrap.shape),
                            dims=id_2D_wrap.dims, coords=id_2D_wrap.coords)

    # Calculate Percent of total MHW area retained
    tot_area = int(np.sum(area.values))
    small_area = area.where(area<=min_area, drop=True)
    small_area = int(np.sum(small_area.values))
    percent_area_kept = 1-(small_area/tot_area)


#     num_2D_features = np.nanmax(keep_labels.values)
#     print('Number of 2D labeled features = \t', num_2D_features)

    ds_out = id_2D_area_bool.to_dataset(name='labels')
    ds_out.attrs['min_area'] = min_area
    ds_out.attrs['percent_area_kept'] = percent_area_kept

    return ds_out

# Cell
def track_3D(da, fieldname):
    '''Track labeled marine heatwaves'''

    # pick a data variable
    data = _check_input(da, fieldname)

    ####### Label with Skimage
    # relabel
    label_sk3, final_features = label_sk(data, connectivity=3, return_num=True)

    # Convert labels to DataArray
    mhw_id_3 = xr.DataArray(label_sk3, dims=['time','lat','lon'],
                                 coords={'time': data.time, 'lat': data.lat,'lon': data.lon})
    mhw_id_3 = mhw_id_3.where(mhw_id_3 != 0, drop=False, other=np.nan)

    print('final features \t', final_features)

    dataout = mhw_id_3.to_dataset(name='labels')
    dataout.attrs['total MHWs'] = final_features
    dataout.attrs['minimum size (km2)'] = data.attrs['min_area']
#     dataout.attrs['minimum size percentile'] = min_size_quartile
    dataout.attrs['fraction of total MHW area kept'] = data.attrs['percent_area_kept']
#     dataout.attrs['temperature threshold percentile'] = threshold
#     dataout.attrs['morphological radius'] = radius
#     dataout.attrs['connectivity'] = connectivity
#     dataout.attrs['resolution'] = res

#     out_path = '/glade/scratch/scanh/MHW_labels/'
#     dataout.to_netcdf(out_path + 'MHWlabels_monthly_OISST_' + outnetCDF, mode='w')

    return dataout


# Cell
class mhw:
    "Label `ssta` using `mhw`"
    def __init__(self, ssta):
        self.ssta = ssta

    def label(self):
        "Assign labels to marine heatwaves"
        return label_2D(self.ssta)

    def track(self):
        "Track identified marine heatwaves from `label` in time"
        return track_2D(self.ssta)
