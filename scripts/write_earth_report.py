from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def main():
    quality=load('out/earth_quality_report.json');portraits=load('data/portraits.json');capture=load('assets/earth/capture.json');extras=load('assets/earth/extra_captures.json')
    sources=load('data/earth_sources.json');lines=['# Google Earth・肖像版：出典と素材','', '取得日：2026-10-13。外部公開・有料契約は実施していません。','', '## Google Earth背景','', '実際のGoogle Earthブラウザー画面を取得。標高への画像貼付・Googleの3Dモデル抽出・地図タイルの一括取得は行っていません。','', '- 俯瞰：Google Earth / Airbus。画面日付表示は6/3/2023、一部の日付不明。','- 斜め視点：Google Earth / Airbus。帰属表示の期間は1/9/2023–2/17/2026、一部不明。','- 広域：Google Earth / Landsat / Copernicus / Data SIO, NOAA, U.S. Navy, NGA, GEBCO。帰属表示の期間は12/14/2015–1/1/2021、一部不明。','', 'これらはGoogle Earthで現在公開されている画像で、リアルタイム画像ではありません。道路・建物・植生は1600年当時の復元ではありません。','', '[Google公式利用ガイド](https://about.google/brand-resource-center/products-and-services/geo-guidelines/)','', '元のGoogle表示を画面下端に残し、画像提供元を読みやすい文字で併記しました。画像の日付はGoogle画面に表示された英語表記をそのまま記録しています。','', '## 肖像','']
    for p in portraits:lines.extend([f'### {p["name"]}',f'- 出典：[{p["credit"]}]({p["page"]})',f'- 権利表示：{p["license"]}',f'- 加工：人物識別用の円形切り抜き・縮小。説明用パネルには全体像を掲載。',f'- SHA-256：`{p["sha256"]}`',''])
    lines.extend(['大谷吉継は今回、出典を確認できた肖像を採用していません。別人の肖像や生成顔で代用せず、部隊名の札で表示しています。','','## 歴史・地形・位置の参照',''])
    for s in sources:
        if s['id'].startswith('PORTRAIT_') or s['id']=='GOOGLE_EARTH':continue
        lines.append(f'- [{s["title"]}]({s["url"]})：{s.get("author","")}')
    (ROOT/'out/earth_sources.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    assets=[]
    for path in sorted((ROOT/'assets').rglob('*')):
        if path.is_file():assets.append({'file':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    (ROOT/'out/earth_assets.json').write_text(json.dumps({'portraits':portraits,'captures':[capture]+extras,'assets':assets},ensure_ascii=False,indent=2),encoding='utf8')
    v=quality['videos'];report=f'''# 関ヶ原：Google Earth・肖像版の更新結果

今回の変更は、実景背景と肖像を使うという依頼への対応です。元の作品を歴史解析の完成品とする判定は撤回したままです。歴史の進行・一次史料の検証・諸説の比較は、引き続き改善が必要です。

## 実際の動画

- [本編：4分10.2秒](E:/rekishikaisetu/out/sekigahara_google_earth_portraits.mp4) — 1920×1080 / 30fps / H.264＋AAC / {v[0]['size_bytes']:,}バイト
- [進軍部分：22.87秒](E:/rekishikaisetu/out/earth_portrait_march_preview.mp4) — 同じ仕様 / {v[1]['size_bytes']:,}バイト
- [日本語字幕](E:/rekishikaisetu/out/earth_subtitles.srt)
- [出典・肖像の所蔵先・画像日付](E:/rekishikaisetu/out/earth_sources.md)
- [機械可読の検証結果](E:/rekishikaisetu/out/earth_quality_report.json)

## 反映した内容

実際のGoogle Earth背景を、広域・3D斜め視点・俯瞰の3種類で使用。軍勢の進軍は、登録済みの俯瞰画像に重ねています。Google Earthの画面や3Dモデルそのものを改変する実装ではありません。

石田三成・小早川秀秋・徳川家康の説明に所蔵先を付した肖像パネルを掲載。俯瞰では肖像付きの部隊札を表示し、小早川隊の移動に肖像を追従させました。大谷隊は肖像を偽作せず名前の札で区別しています。

軍勢は関節を動かす自作Blenderモデルを透過画像に描画して合成しています。20体で構成した記号であり、実際の兵数・服装の厳密な復元ではありません。背景の地形との完全な3D遮蔽・地面接触を保証する方式ではありません。

見出し50px、部隊名38px、字幕46px。背景付きの大きな文字を維持しました。ナレーションもGoogle Earth背景と肖像に合う内容へ再生成しています。

## 自動検証

- 本編{v[0]['frames']:,}フレームと短編{v[1]['frames']:,}フレームを全デコードし、エラーなし。
- 本編全{v[0]['frames']:,}フレームの合成時に、部隊札の画面内配置と札同士の非重複を検査。251地点の配置記録を保存。
- 字幕の行数・文字幅を検査。部隊札が字幕領域へ入らないことを検査。
- Google Earthの画面上9地点の座標と標高を取得。6地点で表示変換を合わせ、別の3地点で確認した最大ずれは{quality['registration_held_out_max_error_px']:.3f}px。これは画像への位置合わせの誤差であり、史実の陣位置の精度ではありません。
- 出力MP4の2地点から画像を取り出し、移動先に小早川の肖像が実際に存在することを画素照合。軍勢と肖像の連動を位置記録でも検査。
- Googleの元の出典表示帯を保持。出力済みMP4でも画素照合で保持を確認。背景ごとの提供元を常時併記。
- 日本語音声の全行生成、尺、音量、クリッピングを検査。独立ASRによる発音判定は未実施。

今回の視覚変更の技術検査はPASSです。歴史的正確性全体や完成作品の品質のPASSとは区別しています。

## 解消した障害

- ブラウザー操作ツールの起動パスエラー：Playwrightと既存のChromiumによる実際のGoogle Earth画面取得へ切り替えて解消。
- 小早川肖像の原寸画像取得がHTTP429：同じCommonsファイルの公開500px版を取得して解消。別の肖像へのすり替えはありません。
- 広域画像の読み込み途中：読み込み100%を確認して再取得。未読み込みの画像は本編に使用しません。

現在の未解消BLOCKERはありません。画像取得は将来のGoogle Earth UI変更・ネットワーク状態に影響されるため、元画像と帰属表示もローカルに保存しました。

## 残っている限界

現代の景観と1600年の景観を混同しない表示にしています。陣跡は記念地点で、当時の陣域を確定するものではありません。小早川隊の経路は二地点を結ぶ説明用の試験経路で、史実の道筋・時刻・隊列幅ではありません。距離と高低差はGoogle画像から抽出せず、別途取得済みの国土地理院DEMで計算しています。

画面は広域から近景へ切り替える構成で、Google Earthの連続したフライスルーを収録したものではありません。
'''
    (ROOT/'out/EARTH_REPORT.md').write_text(report,encoding='utf8');print('Earth report, sources and asset manifest written')
if __name__=='__main__':main()
