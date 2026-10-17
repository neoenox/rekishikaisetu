"""Writes data/season_spec.json."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
spec=dict(slug='season',theme_dir='20261018_season',pack='11_season_distance',header_sub='季節の原因をNASAの解説で確かめる',images={},
 bgm=[['intro','dist','piano36'],['tilt','compare','piano12'],['south','end','piano40']],
 chapters=[
 dict(key='intro',title='夏は、太陽に近いから暑い？',chapter_title='導入：夏は、太陽に近いから暑い？',opener='夏は、太陽に近いから暑い？',opener_until=1,scene=[
   dict(t='chips',y=250,w=640,h=150,gap=160,size=52,items=[dict(at=1,text='夏は暑い'),dict(at=1,text='太陽に近いから？')]),
   dict(t='big',text='近いほど、暖かい？',y=470,at=2,size=60,col='gold'),
   dict(t='panel',box=[120,610,1800,700],text='日本が夏のとき、地球は本当に、太陽に近い？',at=3,size=42,hi=True),
   dict(t='panel',box=[120,730,1800,800],text='資料：NASA（Space Place・Earth Facts・教材）',at=4,size=32)]),
 dict(key='dist',title='地球と太陽の距離は、季節で変わるのか',chapter_title='地球と太陽の距離は、季節で変わるのか',scene=[
   dict(t='panel',box=[60,170,1860,260],title='NASA',text='地球の公転軌道は、完全な円ではない',at=0,size=42),
   dict(t='bars',box=[60,280,1860,560],title='太陽までの距離（NASA Space Place。kmは自作の換算）',unit='万マイル',max=100,lab_w=640,data=[
     dict(at=1,label='近日点（1月） 約1億4,700万km',value=91.4,vlabel='約9,140万マイル',col='org'),dict(at=2,label='遠日点（7月） 約1億5,200万km',value=94.5,vlabel='約9,450万マイル',col='blue')]),
   dict(t='panel',box=[60,580,1860,670],text='北半球が夏の7月に、地球は、太陽から最も遠くなる',at=4,size=44,hi=True,col='gold'),
   dict(t='panel',box=[60,700,1860,800],title='NASA',text='距離が季節の原因ではないことの、証明',at=5,size=42)]),
 dict(key='tilt',title='季節をつくっているのは、何か',chapter_title='季節をつくっているのは、何か',scene=[
   dict(t='panel',box=[60,170,1860,260],title='NASA',text='季節は、地球の、傾いた地軸によって生じる',at=0,size=42,hi=True),
   dict(t='panel',box=[60,280,1860,370],title='地軸の傾き',text='公転面に垂直な方向から、約23.4度',at=1,size=42),
   dict(t='panel',box=[60,390,1860,460],text='公転しているあいだも、同じ方向を向いたまま',at=2,size=36,col='dim'),
   dict(t='panel',box=[60,480,1860,580],title='約6月',text='北極が太陽の方へ傾く → 北半球は夏',at=3,size=42,col='gold'),
   dict(t='panel',box=[60,600,1860,700],title='約12月',text='南極が太陽の方へ傾く → 北半球は冬',at=4,size=42,col='blue'),
   dict(t='panel',box=[60,720,1860,830],title='NASAの教材',text='夏は、昼が長く、太陽の光が、より急な角度で届く',at=5,size=38)]),
 dict(key='compare',title='距離と傾きの、効果を比べる',chapter_title='距離と傾きの、効果を比べる',scene=[
   dict(t='panel',box=[60,160,1860,250],text='簡単な計算（自作）で、距離と傾きの効果を比べる',at=1,until=3,size=42,hi=True),
   dict(t='panel',box=[60,160,1860,250],text='太陽から受ける光の強さは、距離の2乗に反比例',at=3,size=40),
   dict(t='panel',box=[60,265,1860,345],text='近日点 約1億4,700万km／遠日点 約1億5,200万km（9,140万・9,450万マイルから換算）',at=4,size=30,col='dim'),
   dict(t='bars',box=[60,365,930,610],title='距離による日射の差（遠日点＝100）',unit='',max=200,lab_w=190,data=[
     dict(at=5,label='遠日点',value=100,vlabel='100',col='blue'),dict(at=6,label='近日点',value=106.9,vlabel='約107',col='org')]),
   dict(t='panel',box=[60,630,1860,720],text='太陽が高いほど、同じ量の光が、狭い面積に集まる',at=8,until=9,size=42),
   dict(t='bars',box=[990,365,1860,610],title='傾きによる日射の差（冬至＝100）',unit='',max=200,lab_w=190,data=[
     dict(at=9,label='冬至のころ',value=100,vlabel='100',col='blue'),dict(at=10,label='夏至のころ',value=186.9,vlabel='約187',col='org')]),
   dict(t='panel',box=[60,630,1860,720],title='北緯35度の、正午の太陽の高さ',text='夏至のころ 約78度／冬至のころ 約32度',at=9,size=40),
   dict(t='panel',box=[60,735,1860,800],text='傾きの比較の条件：北緯35度・正午・水平な地面／距離は同じ／大気は無視（気温の比ではない）',at=9,size=28,col='dim'),
   dict(t='panel',box=[60,810,1860,862],text='この条件では、傾きによる差 ＞ 距離による差',at=12,size=36,hi=True,col='gold')]),
 dict(key='south',title='では、南半球はどうなのか',chapter_title='では、南半球はどうなのか',scene=[
   dict(t='panel',box=[60,170,1860,260],text='距離が原因なら、地球上のどこでも、同じ時期に夏になるはず',at=0,size=40),
   dict(t='panel',box=[60,280,1860,390],title='NASA',text='地軸が傾き、両極は地球の反対側 → 季節の時期も、反対になる',at=1,size=40,hi=True),
   dict(t='table',box=[60,410,1860,640],cols=['時期','北半球','南半球'],colw=[900,450,450],size=38,rows=[
     dict(at=2,cells=['約6月','夏','冬']),dict(at=4,cells=['約12〜1月（近日点は1月）','冬','夏'])]),
   dict(t='panel',box=[60,670,1860,770],text='傾きで説明できる。距離では説明できない',at=3,size=44,col='gold')]),
 dict(key='end',title='分かること、決められないこと',chapter_title='結論：分かること、決められないこと',scene=[
   dict(t='cols2',size=31,xm=940,xm2=980,left=dict(title='分かること',title_at=0,items=[
      dict(at=1,text='季節の主な原因は、地軸の傾き'),dict(at=2,text='北半球では、冬の1月に最も近く、夏の7月に最も遠い'),dict(at=3,text='近日点と遠日点の光の強さの差は、約7％'),dict(at=4,text='距離を同じにして、北緯35度・正午を比べると、夏至は冬至の約1.9倍（自作の計算）')]),
     right=dict(title='決められないこと',title_at=5,items=[
      dict(at=6,text='距離による光の差（約7％）が、気温を何度変えるか'),dict(at=8,text='各地の実際の気温が、海や大気などでどう決まるか（未確認）')]))])
 ],
 desc=dict(title_main='夏が暑いのは、地球が太陽に近づくからか',title_no=1,
  titles=['夏が暑いのは、地球が太陽に近いから？ NASAの解説と簡単な計算で確かめる','夏は地球が太陽から一番遠い？ 季節の本当の原因','南半球が冬なのはなぜ？ 距離と地軸の傾きを比べる'],
  intro='「夏が暑いのは、地球が太陽に近づくから」。そう思っていませんか。この動画では、NASAの解説と教材から、季節の原因を確かめます。地球と太陽の距離は季節でどう変わるのか(近日点は1月、遠日点は7月)、季節をつくっているのは何か(地軸の傾き)、距離と傾きの効果を簡単な計算でどれくらい違うのか、南半球はどうなのか。分かることと決められないことを、分けて見ていきます。',
  points=['地球の公転軌道は完全な円ではなく、近日点(約9,140万マイル)は1月、遠日点(約9,450万マイル)は7月です。北半球が夏の7月に、地球は太陽から最も遠くなります。NASAは、距離が季節の原因ではないことの証明だとしています(NASA Space Place)。','季節は地軸の傾きによって生じます。地軸は公転面に垂直な方向から約23.4度傾いています(NASA Earth Facts、NASA教材)。北極が太陽の方へ傾く約6月に北半球は夏、南極が太陽の方へ傾く約12月に北半球は冬になります。両極は反対側にあるため、季節の時期も反対です(NASA Space Place)。','NASAの教材は、夏は昼が長く、太陽の光がより急な角度で届くと説明しています。','動画内の「約7パーセント」「約1.9倍」は自作の計算です。距離の差は、太陽から受ける光の強さが距離の2乗に反比例するとして求めた日射の差(近日点は遠日点より約7％強い)。傾きの差は、距離を同じとし、北緯35度の夏至・冬至の正午の太陽の高さ(約78度・約32度)から、水平な地面が受ける光の強さを比べた値(大気は無視、昼の長さは含まない)で、気温の比ではありません。','距離による光の変化が各地の気温を何度変えるのか、各地の実際の気温が海や大気などでどう決まるのかは、この動画では確認していません。'],
  refs=['NASA Space Place「What Causes the Seasons?」:https://spaceplace.nasa.gov/seasons/en/','NASA Science「Earth Facts」:https://science.nasa.gov/earth/facts/','NASA(Goddard)教材 Stargaze「Seasons」:https://cdaweb.gsfc.nasa.gov/pub/documents/archived_websites/pwg.gsfc.nasa.gov/stargaze/Lseason.htm'],
  credit_lines=['・図・グラフ・計算:自作(NASAの公表値を基にした模式図と計算です。外部画像は使用していません)','・サムネイルの背景:Codex(OpenAI)による生成イラスト(地球と太陽のイメージ。実際の縮尺・軌道の再現ではありません)'],
  notes=['距離は、NASA Space Placeのマイル値を、1マイル=約1.609kmとして自作で換算した概算です。','「約7％」「約1.9倍」は、条件(距離を同じ・北緯35度・正午・水平な地面・大気を無視)を置いた自作の計算で、各地の実際の気温や日射量の比ではありません。','誤りがあればコメントでお知らせください。確認のうえ、訂正します。'],
  tags='季節, 夏, 冬, 地軸の傾き, 太陽までの距離, 近日点, 遠日点, 南半球, NASA, 科学, 雑学, 検証',
  checks=['傾きによる日射の差(約1.9倍)と、距離による差(約7％)を、もう一度検算する(`docs/themes/20261018_season/08_fact_check.md`)','NASA Space Place・教材の原文との照合(任意)']),
 thumb=dict(bg='assets/season/thumb_art.png',lines=[['夏は太陽に',90,'white'],['近いから',100,'white'],['暑い？',150,'gold']],sub='NASAの解説で確かめる',y0=14,bar_y=520,bar_w=620,sub_size=44,shade_x=700,shade_w=520))

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
(R/'data'/'season_spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=1),encoding='utf8');print('spec written')
