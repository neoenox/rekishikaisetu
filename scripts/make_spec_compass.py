"""Writes data/compass_spec.json."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
spec=dict(slug='compass',theme_dir='20261018_compass',pack='10_compass_north',header_sub='方位磁針と北極点を確かめる',images={},
 bgm=[['intro','pole','piano12'],['move','decl','piano36'],['end','end','piano40']],
 chapters=[
 dict(key='intro',title='磁針は、北極点を指している？',chapter_title='導入：方位磁針は、北極点を指している？',opener='磁針は、北極点を指している？',opener_until=1,scene=[
   dict(t='chips',y=250,w=640,h=150,gap=160,size=56,items=[dict(at=1,text='地図の北'),dict(at=1,text='磁針の北')]),
   dict(t='big',text='同じ方向？',y=470,at=2,size=64,col='gold'),
   dict(t='panel',box=[120,610,1800,700],text='NOAA・国土地理院の解説で、確かめる',at=3,size=44,hi=True),
   dict(t='panel',box=[120,730,1800,800],text='分かることと、決められないことを、分けて見る',at=4,size=34)]),
 dict(key='what',title='磁針は、何を指しているのか',chapter_title='磁針は、何を指しているのか',scene=[
   dict(t='panel',box=[60,170,1860,280],title='国土地理院',text='方位磁石が指す北を、磁北と呼ぶ',at=0,size=44,hi=True),
   dict(t='panel',box=[60,300,1860,430],title='NOAA',text='方位磁針は、その場所の、磁場の水平な成分の向きを指す',at=1,size=40),
   dict(t='panel',box=[60,450,930,610],title='真北',text='地理上の北極点へ向かう方向',at=2,size=38),
   dict(t='panel',box=[990,450,1860,610],title='磁北',text='真北と、必ずしも一致しない',at=3,size=38,col='gold'),
   dict(t='panel',box=[60,640,1860,730],text='2つの方向のなす角 ＝ 偏角（NOAA）',at=4,size=42,hi=True),
   dict(t='panel',box=[60,750,1860,830],text='地球の自転の極と、地磁気の極は、一致しない（国土地理院）',at=5,size=36,col='dim')]),
 dict(key='pole',title='磁極は、どこにあるのか',chapter_title='磁極は、どこにあるのか',scene=[
   dict(t='panel',box=[60,170,1860,290],title='NOAA：磁極',text='地表で、地磁気が地面に垂直になる位置',at=0,until=5,size=42,hi=True),
   dict(t='panel',box=[60,310,1860,430],title='北の磁極（WMM2025・2025.0年）',text='北緯約85.8度（85.762°）、東経約139度（139.298°）',at=1,until=5,size=40),
   dict(t='panel',box=[60,450,1860,540],text='北極点 ＝ 北緯90度',at=2,until=5,size=42),
   dict(t='bars',box=[60,560,1860,810],title='北極点からの緯度の差（度）。自作の計算（90度 − 緯度）',unit='度',max=10,lab_w=640,data=[
     dict(at=3,label='北の磁極（磁場が垂直）',value=4.238,vlabel='約4.2度（約470 km）',col='org',until=7),dict(at=6,label='地磁気極（双極子モデル）',value=9.15,vlabel='約9.2度（約1,020 km）',col='blue',until=7)]),
   dict(t='panel',box=[60,170,1860,290],title='NOAA：磁極の決め方は、ほかにもある',text='双極子モデルから計算する「地磁気極」は、別の位置（北緯80.85°、西経72.76°。2025.0年）',at=5,size=36),
   ]),
 dict(key='move',title='磁極は、動いている',chapter_title='磁極は、動いている',scene=[
   dict(t='timeline',y=290,x0=160,x1=1760,w=420,size=32,ymax=600,nodes=[
     dict(at=0,x=300,label='1831年',sub='ロスが、カナダ北部で、北の磁極を測定'),dict(at=1,x=760,label='1948〜1994年',sub='カナダの政府機関が、定期的な測量で追跡'),
     dict(at=2,x=1220,label='2001・2007年',sub='国際共同の測量で、地点が追加'),dict(at=3,x=1680,label='2025年（モデル）',sub='北緯85.762°、東経139.298°（北極海のほう）')]),
   dict(t='panel',box=[60,620,1860,700],text='※4つの時点は、間隔を縮めて並べた図（縮尺は一定ではありません）',at=3,size=28,col='dim'),
   dict(t='panel',box=[60,720,1860,790],title='NOAA（PMEL）',text='磁北極は、地理上の決まった位置ではなく、日ごと・年ごとに動く',at=4,size=30),
   dict(t='panel',box=[60,800,1860,860],text='磁針の方位は、真の方位に直して使う必要がある',at=5,size=30,col='gold')]),
 dict(key='decl',title='偏角は、場所と時間で変わる',chapter_title='偏角は、場所と時間で変わる',scene=[
   dict(t='panel',box=[60,170,1860,280],title='偏角（NOAA）',text='磁北と真北のなす角。場所と時間で変わる',at=0,size=42),
   dict(t='panel',box=[60,300,1860,400],title='国土地理院',text='日本は、南鳥島を除く全域が、西偏（磁北が真北より西）',at=2,size=40),
   dict(t='bars',box=[60,420,1860,600],title='磁北が、地図の北より西へずれる大きさ（度）。2020年の磁気図（国土地理院）',unit='度',max=12,lab_w=300,data=[
     dict(at=3,label='札幌',value=10,vlabel='約10度',col='org'),dict(at=3,label='那覇',value=6,vlabel='約6度',col='blue')]),
   dict(t='panel',box=[60,620,1860,730],title='国土地理院（全国平均）',text='1970〜2020年の50年間で、西向きの偏角が約1.4度大きくなった',at=4,size=38),
   dict(t='panel',box=[60,750,1860,830],text='偏角を知らないと、登山などで、地図の向きが合わず、道に迷うおそれ',at=5,size=34,col='gold')]),
 dict(key='end',title='分かること、決められないこと',chapter_title='結論：分かること、調べていないこと',scene=[
   dict(t='cols2',size=33,xm=940,xm2=980,left=dict(title='分かること',title_at=0,items=[
      dict(at=1,text='方位磁針が示すのは、その場所の、磁場の水平な成分の向き'),dict(at=2,text='2025年初めのモデルでは、北の磁極は、北極点から約470 km。位置は、時間とともに変わる'),dict(at=4,text='偏角は、場所と時間で変わる'),dict(at=5,text='方位磁針が北極点を指すとは限らない。示すのは、その場所の磁北')]),
     right=dict(title='今回調べていないこと',title_at=7,items=[
      dict(at=8,text='特定の場所・日時で、真北から何度ずれるか（正確な偏角）')]))])
 ],
 desc=dict(title_main='方位磁針は、本当に北極点を指しているのか',title_no=1,
  titles=['方位磁針は、北極点を指している？ NOAAと国土地理院の解説で確かめる','磁北と真北は、同じ方向？ 偏角と磁極の位置を確かめる','北磁極は、北極点から何km離れている？ 動く磁極の話'],
  intro='「方位磁針は、北極点を指している」。そう思っていませんか。地図の北と、磁針の北は、同じ方向なのでしょうか。この動画では、アメリカの海洋大気庁(NOAA)と国土地理院の解説から、方位磁針が何を指しているのか、磁極は北極点とどれだけ離れているのか、磁極は動くのか、偏角は場所や時間でどう変わるのかを確かめます。分かることと決められないことを、分けて見ていきます。',
  points=['方位磁針は、その場所の磁場の水平な成分の向きを指します(NOAA)。方位磁石が指す北が磁北で、地図の北(真北)と必ずしも一致しません。そのなす角が偏角です(国土地理院、NOAA)。','磁極とは、地表で地磁気が垂直になる位置です。WMM2025(2025.0年)では、北の磁極は北緯85.762度、東経139.298度(NOAA/NCEI)。北極点(北緯90度)との緯度の差は約4.2度で、約470 kmです(自作の計算:4.238度×約111 km)。','NOAAは、磁極の決め方はほかにもあり、双極子モデルから計算する地磁気極は北緯80.85度、西経72.76度(2025.0年)と述べています。','北の磁極は、1831年にカナダ北部で測定され、1948〜1994年のカナダの測量、2001年・2007年の国際共同測量などで追跡されました。NOAAの別の解説は、磁北極は地理上の決まった位置ではなく、日ごと・年ごとに動く、と述べています。','国土地理院によると、日本は南鳥島を除く全域が西偏です。2020年の磁気図では、札幌で約10度、那覇で約6度、西にずれます。全国平均では、1970年から2020年の50年間で、西向きの偏角が約1.4度大きくなりました。'],
  refs=['NOAA/NCEI「Wandering Geomagnetic Poles」:https://www.ncei.noaa.gov/products/wandering-geomagnetic-poles','NOAA/NCEI「Magnetic Declination」:https://www.ngdc.noaa.gov/geomag/declination.shtml','NOAA/PMEL Arctic Zone FAQ:https://www.pmel.noaa.gov/arctic-zone/faq.html','国土地理院「地磁気とは」:https://www.gsi.go.jp/buturisokuchi/menu01_index.html','国土地理院「磁気図2015.0年値」の公表(札幌・那覇の例):https://www.gsi.go.jp/buturisokuchi/magnetic_map2015.html'],
  credit_lines=['・図・グラフ・年表:自作(WMM2025の座標、国土地理院の公表値を基にした模式図と計算です。外部画像は使用していません)','・サムネイルの背景:Codex(OpenAI)による生成イラスト(方位磁針のイメージ。実際の磁場の再現ではありません)'],
  notes=['北磁極の位置・距離は、WMM2025(2025.0年)の座標に基づく概算で、位置は時間とともに変わります。','札幌・那覇の偏角は2020年の磁気図の値で、現在の値とは異なります。','特定の場所・日時の偏角は、国土地理院の磁気図や計算サイトなどで確認してください。','誤りがあればコメントでお知らせください。確認のうえ、訂正します。'],
  tags='方位磁針, 磁北, 真北, 偏角, 北極点, 磁極, 地磁気, 地理, NOAA, 国土地理院, 雑学, 検証',
  checks=['北磁極の座標(WMM2025)と距離(約470 km)の検算を、もう一度行う(`docs/themes/20261018_compass/08_fact_check.md`)','NOAAのページの「直近の測量」の年(任意。動画では使っていない)']),
 thumb=dict(bg='assets/compass/thumb_art.png',lines=[['方位磁針は',90,'white'],['北極点を',100,'white'],['指す？',150,'gold']],sub='NOAAと国土地理院で確かめる',y0=14,bar_y=520,bar_w=620,sub_size=44,shade_x=700,shade_w=520))

def _fit(o):
    if isinstance(o,dict):
        if o.get('t')=='panel' and o.get('title'):
            h=o['box'][3]-o['box'][1]
            if h<112:
                t=o['title']+'：'+o['text'];sz=min(o.get('size',40),40,int((o['box'][2]-o['box'][0]-70)/len(t)))
                if sz>=26:o['title']=None;o['text']=t;o['size']=sz
                else:o['size']=min(o.get('size',40),30)
            else:o['size']=min(o.get('size',40),40 if h<125 else 46)
        for v in o.values():_fit(v)
    elif isinstance(o,list):
        for v in o:_fit(v)
_fit(spec)
(R/'data'/'compass_spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=1),encoding='utf8');print('spec written')
