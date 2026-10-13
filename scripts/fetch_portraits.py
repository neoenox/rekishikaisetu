from pathlib import Path
import requests,json,hashlib,concurrent.futures
root=Path('assets/portraits');root.mkdir(parents=True,exist_ok=True)
items=[dict(id='kobaya',name='小早川秀秋',url='https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Kobayakawa_Hideaki_1.jpg/500px-Kobayakawa_Hideaki_1.jpg',page='https://commons.wikimedia.org/wiki/File:Kobayakawa_Hideaki_1.jpg',credit='小早川秀秋像（一部）／高台寺蔵／作者不詳・17世紀前半／Wikimedia Commons',license='Public Domain / PD-Art',crop=[0,0,1,0.64]),dict(id='ishida',name='石田三成',url='https://upload.wikimedia.org/wikipedia/commons/8/80/Ishida_Mitsunari.jpg',page='https://commons.wikimedia.org/wiki/File:Ishida_Mitsunari.jpg',credit='石田三成像（模本）／東京大学史料編纂所蔵／作者不詳／Wikimedia Commons',license='Public Domain / PD-Art',crop=[0,0,1,0.68]),dict(id='ieyasu',name='徳川家康',url='https://upload.wikimedia.org/wikipedia/commons/1/11/Tokugawa_Ieyasu2.JPG',page='https://commons.wikimedia.org/wiki/File:Tokugawa_Ieyasu2.JPG',credit='徳川家康像／大阪城天守閣／狩野探幽／Wikimedia Commons',license='Public Domain / PD-Japan',crop=[0,0,1,0.7])]
def get(a):
 r=requests.get(a['url'],headers={'User-Agent':'SekigaharaEducationalPoC/1.0'},timeout=60);r.raise_for_status();p=root/(a['id']+'.jpg');p.write_bytes(r.content);a.update(file=str(p),sha256=hashlib.sha256(r.content).hexdigest());print(a['id'],len(r.content),flush=True);return a
with concurrent.futures.ThreadPoolExecutor(3) as pool:items=list(pool.map(get,items))
Path('data/portraits.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf8')


