"""Fetch public-domain portraits/prints from Wikimedia Commons; record license + source page."""
from pathlib import Path
import requests,json,hashlib,time
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'assets'/'portraits';D.mkdir(parents=True,exist_ok=True)
H={'User-Agent':'HonnojiEducationalVideo/1.0 (local, non-commercial)'}
items=[('nobunaga','織田信長','Odanobunaga.jpg'),('mitsuhide','明智光秀','Akechi Mitsuhide2.jpg'),('nobutada','織田信忠','Oda Nobutada3 (cropped).jpg'),('hideyoshi','羽柴秀吉','Toyotomi Hideyoshi (Kodaiji).jpg'),('print','本能寺の変を描いた浮世絵','Honnoj.jpg')]
out=[]
def api(**kw):
    for k in range(6):
        r=requests.get('https://commons.wikimedia.org/w/api.php',params=kw,headers=H,timeout=60)
        try:return r.json()
        except Exception:time.sleep(8*(k+1))
    raise SystemExit('API failed '+str(r.status_code))
for id,name,title in items:
    time.sleep(3);q=api(action='query',titles='File:'+title,prop='imageinfo',iiprop='url|extmetadata',iiurlwidth=1600,format='json')
    info=list(q['query']['pages'].values())[0]['imageinfo'][0];m=info['extmetadata']
    pp=D/f'{id}.jpg'
    if pp.exists() and pp.stat().st_size>50000:r=type('R',(),{'content':pp.read_bytes()})
    else:
        for k in range(8):
            time.sleep(10);r=requests.get(info['thumburl'],headers=H,timeout=120)
            if r.ok:break
            time.sleep(30*(k+1))
        r.raise_for_status();p=D/f'{id}.jpg';p.write_bytes(r.content)
    strip=lambda k:__import__('re').sub('<[^>]+>','',m.get(k,{}).get('value','')).strip()
    out.append(dict(id=id,name=name,file=str(pp.relative_to(ROOT)),page=info['descriptionurl'],license=strip('LicenseShortName'),artist=strip('Artist')[:120],description=strip('ImageDescription')[:200],sha256=hashlib.sha256(r.content).hexdigest()))
    print(id,len(r.content),out[-1]['license'],'|',out[-1]['description'][:80])
(ROOT/'data'/'hn_portraits.json').write_text(json.dumps(out,ensure_ascii=False,indent=1),encoding='utf8')
