from pathlib import Path
import json,math
import numpy as np
from pyproj import Transformer,CRS
from scipy.interpolate import RegularGridInterpolator
ROOT=Path(__file__).resolve().parents[1]
O_LON,O_LAT=135.67,35.00
CRS_=CRS.from_proj4(f'+proj=aeqd +lat_0={O_LAT} +lon_0={O_LON} +datum=WGS84 +units=m')
FWD=Transformer.from_crs(4326,CRS_,always_xy=True)
def xy(lon,lat):return FWD.transform(lon,lat)
# Places. coordinate_basis recorded for the source report. err = assumed positional uncertainty (m), an author assumption.
PLACES={
 'kameyama':dict(name='亀山城',lon=135.5812,lat=35.0136,err=150,basis='Wikipedia 亀山城(丹波国) 記載座標',kind='base'),
 'oinosaka':dict(name='老ノ坂',lon=None,lat=None,err=300,basis='路線上の最高標高点(DEMから算出・仮)',kind='pass'),
 'honnoji':dict(name='本能寺(当時)',lon=135.7534,lat=35.0055,err=150,basis='GSI住所検索: 京都市中京区山田町513(旧地の石碑所在とされる番地。Wikipedia 本能寺)',kind='odawa'),
 'honnoji_now':dict(name='本能寺(現在)',lon=135.768306,lat=35.01028,err=60,basis='Wikipedia 本能寺 記載座標(1591-92年移転後)',kind='now'),
 'nijo':dict(name='二条新御所',lon=135.7580,lat=35.0116,err=250,basis='旧押小路烏丸殿説(Wikipedia 本能寺の変 注47)に基づき、GSI住所検索の御池通烏丸付近で仮置き',kind='odawa'),
}
# schematic army route; NOT a historical road. waypoints chosen from GSI address search (road/town positions)
ROUTE_WP=[('kameyama',135.5812,35.0136),('ouji',135.61731,34.993305),('oinosaka_zone',None,None),('kutsukake',135.646042,34.9842),('tsukahara',135.671875,34.976364),('katsura',135.696701,34.982559),('honnoji',135.7534,35.0055)]
def grid():
    g=np.load(ROOT/'data'/'hn_terrain.npz');return g['xs'],g['ys'],g['h']
def interp():
    xs,ys,h=grid();return RegularGridInterpolator((ys,xs),h)
