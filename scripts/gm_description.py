"""YouTube description draft for the world-map video (chapters from the real timeline + credits + references + pre-publish checklist) -> out/gm_description.md"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
tl=json.loads((ROOT/'data'/'gm_timeline.json').read_text(encoding='utf8'))
def ts(s):s=int(s);return f'{s//60}:{s%60:02d}'
CH={'intro':'アフリカとグリーンランド、どちらが大きい？','why':'なぜ、地図は歪むのか','mercator':'メルカトル図法とは','measure':'歪みを、計算で測る(緯度60度で約4倍、80度で約33倍)','others':'ほかの図法(イコール・アース図法など)','webmap':'ウェブ地図の図法','end':'地図は、間違いなのか(まとめ)'}
chapters=[f'{ts(c["start"])} {CH[c["key"]]}' for c in tl]
dur=tl[-1]['end'];total=f'{int(dur//60)}分{int(dur%60)}秒'
L=['# YouTube 投稿用ドラフト：世界地図は、陸地の大きさを間違えているのか\n',
'## タイトル案',
'1. 世界地図は、陸地の大きさを間違えているのか？【グリーンランドとアフリカ】',
'2. グリーンランドはアフリカに何個入る？ 地図の「大きさ」を計算で検証',
'3. メルカトル図法は間違いなのか？ 面積が4倍・33倍に見える理由を計算する',
'(サムネイルは `out/gm_thumbnail_C.jpg` に決定:グリーンランドをアフリカの中に、真の形と大きさで置いた図。データから描いたもので、生成画像は使っていない。タイトル2と対応。他案はA・B・D=`out/` に保存。)\n',
'## 概要欄(そのまま貼り付け用)\n','```',
'世界地図では、グリーンランドとアフリカが同じくらいの大きさに見えます。実際の面積は約14倍も違います。地図は間違っているのでしょうか？',
'この動画では、球面を平面にするときに必ず起こる歪みを、国の輪郭データと自分で書いた計算で確かめます。メルカトル図法の長所と、面積が大きく見える仕組み(緯度60度で約4倍、80度で約33倍)、面積を保つ図法、ウェブ地図の図法まで。最後に「地図は間違いか」を、分かること／決められないことに分けて考えます。',
'','■ チャプター']+chapters+[
'','■ 動画で使った主な数値',
'・アフリカ 約3,000万km²／グリーンランド 約217万km²(比は約14倍。画面の描画は、Natural Earth 110mの輪郭データから球面上で計算した値で、アフリカ約13.7倍)',
'・メルカトル図法の面積の倍率 ＝ (1÷cos 緯度)²(地球を球体とみなした場合)。緯度60度で4.0倍、80度で約33倍',
'・日本を、球面上で形を変えずに北緯60度付近まで動かすと、メルカトル図法での見かけの面積は約2.6倍(動画内の計算)',
'','■ 出典・クレジット',
'・国・海岸線のデータ:Natural Earth(パブリックドメイン) https://www.naturalearthdata.com/ (110m cultural vectors / Admin 0 - Countries)',
'・地図の描画・図法の計算・グラフ:自作(Python)',
'・音声:VOICEVOX:四国めたん',
'・音楽:魔王魂(https://maou.audio/) ピアノ36 / ピアノ12 / ピアノ40(作曲:森田交一。音量調整・場面に合わせた切り替えを行っています)',
'','■ 参考資料(動画の根拠の確認に使ったもの)',
'・1569年のメルカトル世界地図の書誌(バーゼル大学図書館 e-rara):https://www.e-rara.ch/doi/10.3931/e-rara-25290?lang=fr',
'・Equal Earth図法(PROJの解説):https://proj.org/en/stable/operations/projections/eqearth.html',
'・ウェブ地図のタイル方式(Microsoft Bing Maps Tile System):https://learn.microsoft.com/en-us/bingmaps/articles/bing-maps-tile-system',
'・地図投影法の解説(USGS):https://www.usgs.gov/publications/map-projections',
'','■ 注意',
'・画面の国境線は、データの既定の線で、国境や領有に関する立場を示すものではありません。',
'・数値の一部(1569年の題名、ウェブ地図の採用理由など)は、公開資料で確認した範囲での説明です。誤りがあればコメントでお知らせください。',
'・動画内には出典・クレジットを表記せず、この概要欄にまとめています。',
'```\n',
'## タグ案','世界地図, メルカトル図法, 地図, 図法, グリーンランド, アフリカ, イコールアース, 地理, 雑学, 数学, ウェブメルカトル, 面積, 思い込み, 検証\n',
'## 投稿前チェック(自分で確認が必要)',
'- [ ] **動画を通しで見る・聞く**(動き、ナレーションの読み、BGMの音量。査読者は、動きと音声を確認できていない)',
'- [ ] 概要欄のURL(特にUSGS・Natural Earth。自動の確認では403/406で応答したが、ブラウザで開けるか)',
'- [ ] Natural Earthの利用条件(パブリックドメイン、クレジット不要の旨)を、投稿日に再確認し、スクリーンショットを保存',
'- [ ] VOICEVOX:四国めたん の最新規約',
'- [ ] BGM(魔王魂 ピアノ36/12/40)の最新の利用規約。Content IDの誤検出に備え、取得記録を保存',
'- [ ] YouTubeの「改変または合成されたコンテンツ」の設問(合成音声を使用。生成画像は、動画・サムネイルとも不使用)',
'- [ ] 一次確認が残る項目:1569年の地図の題名(e-rara)、ウェブ地図の採用理由(Microsoft)、2017年のボストンの件、球面の平面化の不可能性(USGS)。詳しくは `docs/themes/20261016_channel_launch/08_fact_check.md`',
'- [ ] 字幕:`out/gm_subtitles.srt` をアップロード(日本語)',
'- [ ] サムネイル:`out/gm_thumbnail_C.jpg`(1280x720、JPEG、約150KB)','']
(ROOT/'out'/'gm_description.md').write_text('\n'.join(L)+'\n',encoding='utf8');print('\n'.join(chapters),'\nduration',total)
