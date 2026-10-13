"""Source-led storyboard. No generated claim is promoted to historical fact."""
from pathlib import Path
import json,re,html,requests,hashlib
from pyproj import Transformer,CRS
ROOT=Path(__file__).resolve().parents[1]
def save(name,obj): (ROOT/'data'/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8')
sources=[
 ('GSI_DEM','国土地理院','標高タイル仕様','https://cyberjapandata.gsi.go.jp/development/demtile.html','PNG復号式・無効値','国土地理院コンテンツ利用規約・出典表示。標高を加工。'),
 ('GSI_TERMS','国土地理院','地理院タイル利用','https://maps.gsi.go.jp/help/use.html','利用規約','地理院タイル（標高）を加工して作成'),
 ('MUSEUM','岐阜関ケ原古戦場記念館','記念館紹介','https://sekigahara.pref.gifu.lg.jp/','記念館とは：慶長五年（1600年）','事実参照と自作要約のみ。写真・地図・文章の転載なし。'),
 ('ISHIDA','岐阜関ケ原古戦場記念館','石田三成コース','https://sekigahara.pref.gifu.lg.jp/ishida-mitsunari/','石田三成陣跡・大谷吉継陣跡','事実参照・自作要約。一次史料の直接校訂は未実施。'),
 ('KOBAYA','岐阜関ケ原古戦場記念館','小早川秀秋コース','https://sekigahara.pref.gifu.lg.jp/kobayakawa-hideaki/','小早川秀秋陣跡','事実参照・自作要約。'),
 ('IEYASU','岐阜関ケ原古戦場記念館','徳川家康コース','https://sekigahara.pref.gifu.lg.jp/tokugawa-ieyasu/','最初陣地・最後陣地','事実参照・自作要約。時刻と威嚇射撃は確定扱いしない。'),
 ('REKIMIN','関ケ原町歴史民俗学習館','文化財・陣跡マップ','https://rekimin-sekigahara.jp/main/map/','陣跡マップ説明','地図画像は不使用。曖昧な位置が省略されるとの説明を参照。'),
 ('LOC','株式会社CCL 大垣支社','関ヶ原位置情報リスト2013年度','https://linkdata.org/work/rdf1s884i/SekigaharaLocationData.html','名称・緯度経度の列のみ','CC BY 3.0 https://creativecommons.org/licenses/by/3.0/deed.ja 位置を局所座標へ変換。歴史記述・画像は不使用。'),
 ('VOICE','VOICEVOX','利用規約','https://voicevox.hiroshiba.jp/term/','クレジット表記','VOICEVOX:四国めたん。音声規約はengine speaker_infoのpolicyを保存。'),
 ('REMOTION','Remotion AG','License & Pricing','https://www.remotion.dev/docs/license/pricing','個人・3人以下無料枠','個人ローカルPoC。外部サービス化・公開なし。'),
 ('METHOD','本PoC','解析仕様','local:README.md','経路距離・勾配・速度感度分析','独自実装。歴史資料ではない。')]
def main():
    records=[]
    for id,author,title,url,section,rights in sources:
        rec=dict(id=id,author=author,title=title,url=url,section=section,rights=rights,acquired='2026-10-13')
        if url.startswith('https:'):
            p=ROOT/'cache'/f'source_{id}.html'
            if not p.exists():
                r=requests.get(url,timeout=90);r.raise_for_status();p.write_bytes(r.content)
            rec['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
        records.append(rec)
    save('sources.json',records)
    raw=(ROOT/'cache'/'source_LOC.html').read_text(encoding='utf8')
    rows=[]
    for tr in re.findall(r'<tr\b[^>]*>(.*?)</tr\s*>',raw,re.S):
        cells=[html.unescape(re.sub('<[^>]+>','',td)).strip() for td in re.findall(r'<td\b[^>]*>(.*?)</td\s*>',tr,re.S)]
        if cells:rows.append(cells)
    crs=CRS.from_proj4('+proj=aeqd +lat_0=35.355 +lon_0=136.472 +datum=WGS84 +units=m')
    transform=Transformer.from_crs(4326,crs,always_xy=True)
    units=[]
    for id,name,key,side,source in [('ishida','石田三成','笹尾山','west','ISHIDA'),('kobaya','小早川秀秋','松尾山','conditional','KOBAYA'),('otani','大谷吉継','大谷吉継 陣跡','west','ISHIDA'),('ieyasu','徳川家康','桃配山','east','IEYASU')]:
        row=next(r for r in rows if len(r)>6 and key in r[1]);lat,lon=float(row[5]),float(row[6]);x,y=transform.transform(lon,lat)
        units.append(dict(id=id,name=name,side=side,lat=lat,lon=lon,x_m=x,y_m=y,position_error_m=150,position_type='inferred',coordinate_basis='LOC row '+row[0]+' '+row[1]+'; present-day monument, not verified 1600 occupied footprint',source_ids=[source,'LOC'],troop_count_range=None,alternatives='陣域・人数・正確な時刻は復元しない',symbol_scale='旗100m・兵士24mの説明用拡大。実数・実寸ではない'))
    save('units.json',units)
    scenes=[
      ('関ヶ原を、地形から読む','史料参照＋現代実測地形',['MUSEUM','GSI_DEM'],'慶長五年、千六百年。関ヶ原の戦いを、地形から読み解きます。画面は国土地理院の標高データによる現代の地形です。合戦当日の完全な復元ではありません。史料の説明、位置の推定、そして分析上の仮説を、分けて見ていきましょう。'),
      ('01 / 地形の骨格','現代DEM｜高さの誇張なし',['GSI_DEM','METHOD'],'まず、盆地と周囲の起伏に注目します。水平距離と標高は、ともにメートル単位で、高さの誇張はしていません。谷筋と丘陵の並びは、移動を考える基礎になります。ただし、現代の標高から、当時の道や川幅まで確定することはできません。'),
      ('02 / 陣跡と陣域を分ける','位置推定｜誤差半径150mは仮定',['REKIMIN','LOC'],'次に、陣跡の位置を重ねます。座標は公開された位置情報を参照しました。陣跡の記念地点は、当時の軍勢が占めた範囲そのものではありません。ここでは百五十メートルの誤差範囲を仮置きします。旗の大きさも、見やすくした象徴表現です。'),
      ('03 / 笹尾山の石田三成','史料参照｜陣域・視界は未確定',['ISHIDA','LOC'],'記念館の史跡案内では、石田三成の陣は笹尾山に置かれたと説明されています。高い地点から周辺を見渡す、という地形上の特徴を確認できます。ただし、木々や天候が視界に与えた影響は不明です。高さだけで、指揮の優劣を決めることはできません。'),
      ('04 / 松尾山と大谷隊','史料参照｜攻撃経路は模式',['KOBAYA','ISHIDA'],'南側の松尾山は、小早川秀秋の陣跡として紹介されています。記念館は、小早川隊の行動と大谷隊への攻撃を説明しています。ここで動く矢印は、その関係を示す模式表現です。実際に歩いた道筋や、隊列の幅を復元したものではありません。'),
      ('05 / 本陣の移動','史料参照｜分単位の時刻を省略',['IEYASU'],'徳川家康については、桃配山の最初の陣地から、前方の最後の陣地へ移ったと、記念館が紹介しています。本編では、詳しい時刻の断定を避けます。移動には、観察場所が変わる効果と、移動時間が必要になる側面があります。両方を分けて考えます。'),
      ('06 / 地面に沿う進軍','仮説モデル｜史実の経路ではない',['GSI_DEM','METHOD'],'ここからは仮説モデルです。小早川の陣跡から大谷の陣跡へ、二点を結ぶ試験経路を設定します。矢印と隊列は、標高面に沿って進みます。画面の動きは時間を圧縮したものです。当時の進軍速度や戦闘の展開を、そのまま表してはいません。'),
      ('07 / 距離と勾配を測る','解析｜現代DEM・仮定経路',['GSI_DEM','METHOD'],'経路に沿って、水平距離、登りの量、下りの量を測ります。水平距離が同じでも、起伏があれば移動の条件は変わります。ここでの計算は、地面の形を調べるためのものです。道の有無やぬかるみ、敵との接触を計算に入れていない点に注意が必要です。'),
      ('08 / 速度を変えたら','反実仮想｜移動時間のみ',['METHOD'],'次は、速度を変える感度分析です。毎秒〇点五メートル、一メートル、一点五メートルという三つの仮定で、同じ距離を割ります。これは移動時間だけの比較です。どの速度が当日の軍勢に正しかったかは判断できず、この数字から勝率を出すこともできません。'),
      ('09 / わからないことを残す','論争・不明｜確定的演出を避ける',['IEYASU','REKIMIN'],'家康による小早川への威嚇射撃は、記念館でも一説として説明されています。本編では、その射撃を確定した出来事として再現しません。兵数、攻撃開始の正確な時刻、詳しい陣域も省略しました。わからない部分を残すことが、解析の信頼性を守ります。'),
      ('10 / 地形は条件、結果は別','解析の限界｜勝敗モデルなし',['METHOD'],'地形の起伏と距離は、戦略を考える条件の一つです。しかし、指揮、情報、忠誠、士気といった要素は、この地形モデルだけでは測れません。三次元で見えることと、歴史的に証明されたことは別です。この試作は、問いを整理する道具として使います。'),
      ('出典・制作クレジット','国土地理院DEMを加工｜VOICEVOX:四国めたん',['GSI_DEM','ISHIDA','KOBAYA','IEYASU','LOC','VOICE'],'地形は国土地理院の標高タイルを加工しました。歴史の説明は、岐阜関ヶ原古戦場記念館と関ヶ原町歴史民俗学習館を参照。位置情報は、株式会社シーシーエル大垣支社の公開データを利用しています。音声は、ボイスボックス、四国めたんです。')]
    save('scenes.json',[dict(id=i,title=t,category=c,source_ids=s,narration=n,visual_phase=i/11) for i,(t,c,s,n) in enumerate(scenes)])
    save('events.json',[dict(id='symbolic_march',unit_id='kobaya',type='illustrative',time_historical=None,from_unit='kobaya',to_unit='otani',source_ids=['ISHIDA','METHOD'],note='Relations based on museum narrative; straight interpolated route is invented for terrain conformance test; video compresses 3600s model time into 25s')])
    save('pronunciations.json',{'関ヶ原':'セキガハラ','関ケ原':'セキガハラ','笹尾山':'ササオヤマ','松尾山':'マツオヤマ','桃配山':'モモクバリヤマ','石田三成':'イシダミツナリ','小早川秀秋':'コバヤカワヒデアキ','大谷吉継':'オオタニヨシツグ','徳川家康':'トクガワイエヤス','四国めたん':'シコクメタン','VOICEVOX':'ボイスボックス','DEM':'ディーイーエム'})
    save('assumptions.json',{'historical_certification':'Official museum summaries are attributed accounts, not primary-document proof. No contested narrative promoted to confirmed.','coordinate_uncertainty_m':150,'coordinate_uncertainty_basis':'author assumption, not measured error','route':'straight endpoint interpolation; not historic road','model_seconds':3600,'screen_seconds':25,'troop_count':'not represented; identical 30 symbols per formation','vegetation':'procedural illustration; not historic reconstruction','weather':'cinematic fog only; not historic weather claim','visibility':'not computed; canopy/weather unknown','vertical_scale':1,'terrain':'modern DEM, not a 1600 survey','speed_sensitivity_m_s':[.5,1,1.5]})
    print('story scenes',len(scenes),'units',[(u['id'],u['lat'],u['lon']) for u in units])
if __name__=='__main__':main()
