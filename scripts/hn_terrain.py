"""Honnoji: GSI DEM (dem_png z14) + GSI seamlessphoto texture over Kameyama-Kyoto. No hole filling."""
from pathlib import Path
import io,json,math,hashlib
import numpy as np,requests
from PIL import Image
from pyproj import Transformer,CRS
from scipy.ndimage import map_coordinates
ROOT=Path(__file__).resolve().parents[1]
O_LON,O_LAT=135.67,35.00
BOUNDS=[135.545,34.955,135.800,35.045]  # lon0,lat0,lon1,lat1
STEP=30.
def tile(lon,lat,z):return (lon+180)/360*2**z,(1-np.arcsinh(np.tan(np.radians(lat)))/math.pi)/2*2**z
def decode(rgb):
    a=np.asarray(rgb,dtype=np.int32);n=a[...,0]*65536+a[...,1]*256+a[...,2]
    return np.where(n==8388608,np.nan,np.where(n>8388608,n-16777216,n)*.01)
def fetch(layer,ext,z,x,y,folder):
    p=folder/f'{layer}_{z}_{x}_{y}.{ext}'
    if not p.exists():
        r=requests.get(f'https://cyberjapandata.gsi.go.jp/xyz/{layer}/{z}/{x}/{y}.{ext}',timeout=60);r.raise_for_status();p.write_bytes(r.content)
    return p.read_bytes()
def main():
    z=14;folder=ROOT/'cache'/'hn_tiles';folder.mkdir(parents=True,exist_ok=True)
    x0,y0=map(math.floor,tile(BOUNDS[0],BOUNDS[3],z));x1,y1=map(math.floor,tile(BOUNDS[2],BOUNDS[1],z))
    W=(x1-x0+1)*256;H=(y1-y0+1)*256;mosaic=np.full((H,W),np.nan);photo=Image.new('RGB',(W,H));manifest=[]
    for y in range(y0,y1+1):
        for x in range(x0,x1+1):
            raw=fetch('dem_png','png',z,x,y,folder);a=decode(Image.open(io.BytesIO(raw)).convert('RGB'))
            mosaic[(y-y0)*256:(y-y0+1)*256,(x-x0)*256:(x-x0+1)*256]=a
            pr=fetch('seamlessphoto','jpg',z,x,y,folder);photo.paste(Image.open(io.BytesIO(pr)).convert('RGB'),((x-x0)*256,(y-y0)*256))
            manifest.append({'dem_sha256':hashlib.sha256(raw).hexdigest(),'x':x,'y':y,'nodata':int(np.isnan(a).sum())})
    nod=int(np.isnan(mosaic).sum());print('tiles',len(manifest),'nodata px',nod)
    # sea/no data tiles absent here; fill only isolated nodata with 0 is NOT done: report
    assert nod==0,'DEM nodata'
    crs=CRS.from_proj4(f'+proj=aeqd +lat_0={O_LAT} +lon_0={O_LON} +datum=WGS84 +units=m')
    fwd=Transformer.from_crs(4326,crs,always_xy=True);inv=Transformer.from_crs(crs,4326,always_xy=True)
    xmin,ymin=fwd.transform(BOUNDS[0]+.003,BOUNDS[1]+.003);xmax,ymax=fwd.transform(BOUNDS[2]-.003,BOUNDS[3]-.003)
    xs=np.arange(math.ceil(xmin/STEP)*STEP,xmax,STEP);ys=np.arange(math.ceil(ymin/STEP)*STEP,ymax,STEP)
    xx,yy=np.meshgrid(xs,ys);lon,lat=inv.transform(xx,yy);tx,ty=tile(lon,lat,z)
    px=(tx-x0)*256-.5;py=(ty-y0)*256-.5
    assert px.min()>=0 and py.min()>=0 and px.max()<W-1 and py.max()<H-1
    h=map_coordinates(mosaic,[py,px],order=1);np.savez(ROOT/'data'/'hn_terrain.npz',xs=xs,ys=ys,h=h)
    # texture: resample photo to metric grid orientation (north up), 1 px = 15 m
    tw,th=int((xs[-1]-xs[0])/9),int((ys[-1]-ys[0])/9)
    gx=np.linspace(xs[0],xs[-1],tw);gy=np.linspace(ys[-1],ys[0],th);GX,GY=np.meshgrid(gx,gy);lo,la=inv.transform(GX,GY);ttx,tty=tile(lo,la,z)
    arr=np.asarray(photo,dtype=float);out=np.stack([map_coordinates(arr[...,c],[(tty-y0)*256-.5,(ttx-x0)*256-.5],order=1) for c in range(3)],-1)
    Image.fromarray(out.clip(0,255).astype(np.uint8)).save(ROOT/'cache'/'hn_texture.png')
    info={'layers':['dem_png','seamlessphoto'],'zoom':z,'origin_lonlat':[O_LON,O_LAT],'step_m':STEP,'grid':[len(xs),len(ys)],'extent_m':[float(xs[0]),float(xs[-1]),float(ys[0]),float(ys[-1])],'height_min_m':float(h.min()),'height_max_m':float(h.max()),'vertical_scale':1,'tiles':manifest,'notice':'Modern DEM and modern aerial photo; 1582 topography/land use differ.'}
    (ROOT/'data'/'hn_terrain_manifest.json').write_text(json.dumps(info,indent=1),encoding='utf8')
    print({k:v for k,v in info.items() if k!='tiles'})
if __name__=='__main__':main()
