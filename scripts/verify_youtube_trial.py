from pathlib import Path
import sys,json,subprocess,hashlib,re,numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).parent))
from build_youtube_trial import Trial
ROOT=Path(__file__).resolve().parents[1]
def run(args):
 p=subprocess.run(args,capture_output=True);assert p.returncode==0,p.stderr.decode(errors='replace');return p
f=Trial();path=ROOT/'out/sekigahara_youtube_trial.mp4';meta=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]).stdout);v=next(x for x in meta['streams'] if x['codec_type']=='video');a=next(x for x in meta['streams'] if x['codec_type']=='audio');assert (v['width'],v['height'],v['r_frame_rate'],v['codec_name'],a['codec_name'])==(1920,1080,'30/1','h264','aac');assert int(v['nb_frames'])==round(f.audio['total_seconds']*30)
run(['ffmpeg','-v','error','-i',str(path),'-f','null','-'])
loud=run(['ffmpeg','-hide_banner','-i',str(path),'-vn','-af','ebur128=peak=true','-f','null','-']).stderr.decode(errors='replace');(ROOT/'logs/trial_loudness.log').write_text(loud,encoding='utf8');summary=loud[loud.rfind('Summary:'):];integrated=float(re.search(r'I:\s*([-\d.]+) LUFS',summary)[1]);true_peak=float(re.search(r'Peak:\s*([-\d.]+) dBFS',summary)[1]);assert -19<integrated<-17 and true_peak<0,(integrated,true_peak)
layouts=json.loads((ROOT/'out/trial_layout.json').read_text(encoding='utf8'));p3=[x['progress'] for x in layouts if x['scene']==3];assert all(a<=b for a,b in zip(p3,p3[1:]));assert all(abs(x['progress']-.7)<1e-9 for x in layouts if x['scene'] in [4,5]);assert all(x['explicit_reset'] for x in layouts if x['scene']==1);assert all(len(c['text'])<=28 for c in f.captions)
checks=[]
for s in f.scenes:
 frame=round((s['start']+s['duration']/2)*30);snap=ROOT/'out'/f'trial_encoded_scene_{s["id"]}.png';run(['ffmpeg','-y','-v','error','-ss',str(frame/30),'-i',str(path),'-frames:v','1',str(snap)]);im=Image.open(snap).convert('RGB');reference=f.frame(frame).convert('RGB');mae=float(np.abs(np.asarray(im).astype(float)-np.asarray(reference).astype(float)).mean());assert mae<12
 for box in [(0,200,20,800),(0,1015,1200,1030)]:assert np.asarray(im.crop(box)).std()>10,'Black edge or band'
 checks.append(dict(scene=s['id'],frame=frame,encoded_rgb_mae=mae))
sources=json.loads((ROOT/'data/earth_sources.json').read_text(encoding='utf8'));ids={s['id'] for s in sources};assert all(set(s['source_ids'])<=ids for s in f.scenes)
report=dict(status='PASS_FOR_EDITORIAL_TRIAL',file=path.name,seconds=float(meta['format']['duration']),frames=int(v['nb_frames']),resolution=[1920,1080],fps=30,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),integrated_lufs=integrated,true_peak_dbfs=true_peak,fully_decoded=True,all_frame_card_bounds_checked=True,short_subtitle_chunks=len(f.captions),encoded_frame_checks=checks,motion_continuity='Only explicitly labelled teaser reset; progress retained after main march',limits=['Illustrative route, not historical path or timing','Background is modern imagery','Portrait tracking and map sprites are2D compositing','No independent pronunciation ASR or audience retention measurement'])
(ROOT/'out/trial_quality_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
credit=['小早川秀秋と大谷隊の位置関係を、現代の景観と陣跡座標から読むお試し動画です。','背景は現代の画像、進軍は二地点を結ぶ模式表現です。実際の経路・兵数・時刻の復元ではありません。','','【チャプター】']
for s in f.scenes:
 seconds=int(s['start']);credit.append(f'{seconds//60:02}:{seconds%60:02} {s["title"]}')
credit+=['','音声：VOICEVOX:四国めたん','背景：Google Earth / Airbus','肖像：小早川秀秋像（一部）、高台寺蔵、作者不詳・17世紀前半','Wikimedia Commons / Public Domain','https://commons.wikimedia.org/wiki/File:Kobayakawa_Hideaki_1.jpg','位置情報：株式会社CCL 大垣支社、CC BY3.0。座標変換・説明用配置に加工。','地形解析：国土地理院 地理院タイル（標高）を加工。','','【参照】']
for s in sources:
 if s['id'] in ['KOBAYA','LOC','GSI_DEM','REKIMIN']:credit += [s['title'],s['url']]
credit+=['https://voicevox.hiroshiba.jp/','https://zunko.jp/con_ongen_kiyaku.html','https://about.google/brand-resource-center/products-and-services/geo-guidelines/']
(ROOT/'out/trial_video_description.txt').write_text('\n'.join(credit)+'\n',encoding='utf8')
(ROOT/'out/TRIAL_REPORT.md').write_text(f'''# 編集改善のお試し版

[動画](E:/rekishikaisetu/out/sekigahara_youtube_trial.mp4)／[概要欄](E:/rekishikaisetu/out/trial_video_description.txt)／[検証JSON](E:/rekishikaisetu/out/trial_quality_report.json)

尺：{report['seconds']:.2f}秒。1080p30fps、H.264/AAC。既存の3分44秒版は上書きしていません。

冒頭から動きを見せ、小早川・大谷の2隊へ話題を限定。全景、斜め視点、位置関係へ寄る構図を切り替えました。字幕を最大28文字の短い区間へ分割し、機能紹介を削って位置関係と起伏の説明に変更。全景へ戻っても部隊の進軍状態を保持し、冒頭の先取りから初期配置へ戻す箇所は画面で明示しました。

上下の帯は使わず、必須のGoogle出典だけ小さく表示。制作クレジットは概要欄へ保存しています。

全{report['frames']}フレームをデコード。全フレーム合成時の部隊札の配置を検査。6場面の実動画を取り出して合成元と画素照合し、余白・出典・字幕・肖像を含む画面を確認。音量は実MP4で{integrated:.1f} LUFS、トゥルーピーク{true_peak:.1f} dBFSでした。

経路は模式表現で、歴史的な経路・兵数・時刻を断定しません。字幕区間は文中の文字量で配分しており、独立ASRによる発音・音素位置の確認は未実施です。視聴維持率や作品の完成度を保証する検査ではありません。
''',encoding='utf8')
print('TRIAL PASS',report['seconds'],'seconds',integrated,'LUFS',true_peak,'dBFS')
