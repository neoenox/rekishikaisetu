"""GSI 'ort' (latest orthophoto, no seamless mosaic haze patches): z15 base + z17 feathered patch around central Kyoto."""
from pathlib import Path
import io,json,math
import numpy as np,requests
from PIL import Image
from pyproj import Transformer
from scipy.ndimage import map_coordinates
from hn_common import ROOT,CRS_
INV=Transformer.from_crs(CRS_,4326,always_xy=True)
def tile(lon,lat,z):return (lon+180)/360*2**z,(1-np.arcsinh(np.tan(np.radians(lat)))/np.pi)/2*2**z
def mosaic(z,lonlat_bounds):
    folder=ROOT/'cache'/'hn_tiles';x0,y0=[int(v) for v in np.floor(tile(lonlat_bounds[0],lonlat_bounds[3],z))];x1,y1=[int(v) for v in np.floor(tile(lonlat_bounds[2],lonlat_bounds[1],z))]
    im=Image.new('RGB',((x1-x0+1)*256,(y1-y0+1)*256))
    for y in range(y0,y1+1):
        for x in range(x0,x1+1):
            p=folder/f'ort_{z}_{x}_{y}.jpg'
            if not p.exists():
                r=requests.get(f'https://cyberjapandata.gsi.go.jp/xyz/ort/{z}/{x}/{y}.jpg',timeout=60);r.raise_for_status();p.write_bytes(r.content)
            im.paste(Image.open(p).convert('RGB'),((x-x0)*256,(y-y0)*256))
    print('z',z,'tiles',(x1-x0+1)*(y1-y0+1),flush=True);return np.asarray(im,dtype=float),x0,y0
def resample(arr,x0,y0,z,ext,px_m):
    xmin,xmax,ymin,ymax=ext;tw=int((xmax-xmin)/px_m);th=int((ymax-ymin)/px_m)
    gx=np.linspace(xmin,xmax,tw);gy=np.linspace(ymax,ymin,th);GX,GY=np.meshgrid(gx,gy);lo,la=INV.transform(GX,GY);tx,ty=tile(lo,la,z)
    return np.stack([map_coordinates(arr[...,c],[(ty-y0)*256-.5,(tx-x0)*256-.5],order=1) for c in range(3)],-1)
def main():
    info=json.loads((ROOT/'data'/'hn_terrain_manifest.json').read_text());ext=info['extent_m']
    lo0,la0=INV.transform(ext[0],ext[2]);lo1,la1=INV.transform(ext[1],ext[3])
    arr,x0,y0=mosaic(15,[lo0-.002,la0-.002,lo1+.002,la1+.002]);base=resample(arr,x0,y0,15,ext,6)
    Image.fromarray(base.clip(0,255).astype(np.uint8)).save(ROOT/'cache'/'hn_texture.png');print('base',base.shape)
    # central patch (metres, local aeqd): covers old/new Honnoji and Nijo
    from hn_common import xy
    xa,ya=xy(135.746,35.0005);xb,yb=xy(135.775,35.0160);pe=[xa,xb,ya,yb]
    arr2,x0,y0=mosaic(17,[135.744,34.999,135.777,35.0175]);patch=resample(arr2,x0,y0,17,pe,1.2)
    h,w=patch.shape[:2];yy,xx=np.mgrid[0:h,0:w];edge=np.minimum(np.minimum(xx,w-1-xx),np.minimum(yy,h-1-yy)).astype(float);alpha=np.clip(edge/140,0,1)**1.5*255
    rgba=np.dstack([patch.clip(0,255),alpha]).astype(np.uint8);Image.fromarray(rgba,'RGBA').save(ROOT/'cache'/'hn_patch.png');print('patch',rgba.shape,pe)
    json.dump(dict(extent_m=pe,px_m=1.2,zoom=17,layer='ort'),open(ROOT/'data'/'hn_patch.json','w'))
    info.update(layers=['dem_png','ort'],texture='ort z15 base (6 m/px) + z17 patch (1.2 m/px)');(ROOT/'data'/'hn_terrain_manifest.json').write_text(json.dumps(info,indent=1),encoding='utf8')
if __name__=='__main__':main()
