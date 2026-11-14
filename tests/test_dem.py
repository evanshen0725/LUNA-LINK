import numpy as np
import rasterio
from rasterio.transform import from_origin
from backend.app.dem import inspect_dem, terrain_horizon

def test_dem_metadata_and_horizon(tmp_path):
    path=tmp_path/'synthetic.tif'
    arr=np.zeros((101,101),dtype='float32')
    # A 10 m high ridge 100 m north of observer
    arr[39:42,:]=10
    with rasterio.open(path,'w',driver='GTiff',height=101,width=101,count=1,dtype='float32',crs='EPSG:3857',transform=from_origin(-500,500,10,10),nodata=-9999) as ds:
        ds.write(arr,1)
    meta=inspect_dem(str(path))
    assert meta['width']==101 and meta['valid_pixels']==10201
    result=terrain_horizon(str(path),0,0,[0,90,180,270],max_distance_m=300,step_m=10)
    north=next(x for x in result['profile'] if x['azimuth_deg']==0)
    assert north['horizon_elevation_deg']>0
