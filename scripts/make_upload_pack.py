"""Build upload-ready folders, one per video, files placed flat (no sub-folders) from the generated outputs (copies; sources stay in out/).
upload/<video>/  video.mp4  thumbnail.jpg  subtitles_ja.srt  title.txt  title_alternatives.txt  description.txt  tags.txt
usage: python scripts/make_upload_pack.py   -> rebuilds every pack listed in PACKS"""
import re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];UP=ROOT/'upload'
PACKS={
 '01_world_map_distortion':dict(video='out/gm_video.mp4',thumb='out/gm_thumbnail_C.jpg',srt='out/gm_subtitles.srt',desc='out/gm_description.md',title_no=2),
 '02_honnoji_incident':dict(video='out/honnoji.mp4',thumb='out/thumbnail_A.jpg',srt='out/hn_subtitles.srt',desc='out/youtube_description.md',title_no=1),
 '03_ninja_myths':dict(video='out/nj_video.mp4',thumb='out/nj_thumbnail_A.jpg',srt='out/nj_subtitles.srt',desc='out/nj_description.md',title_no=1),
}
def sections(md):
    """-> (titles list, description body, tags line) from the generated description draft"""
    titles=[re.sub(r'^\d+\. ','',l) for l in md.split('## 概要欄')[0].split('## タイトル案')[1].split('\n') if re.match(r'^\d+\. ',l)]
    body=md.split('## 概要欄')[1].split('```')[1].strip('\n')
    tags=[l for l in md.split('## タグ案')[1].split('\n') if l.strip()][0].strip()
    return titles,body,tags
def build(name,cfg):
    D=UP/name;D.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ROOT/cfg['video'],D/'video.mp4');shutil.copyfile(ROOT/cfg['thumb'],D/'thumbnail.jpg');shutil.copyfile(ROOT/cfg['srt'],D/'subtitles_ja.srt')
    titles,body,tags=sections((ROOT/cfg['desc']).read_text(encoding='utf8'))
    (D/'title.txt').write_text(titles[cfg['title_no']-1]+'\n',encoding='utf8')
    (D/'title_alternatives.txt').write_text('\n'.join(f'{i+1}. {t}' for i,t in enumerate(titles))+'\n',encoding='utf8')
    (D/'description.txt').write_text(body+'\n',encoding='utf8')
    (D/'tags.txt').write_text(tags+'\n',encoding='utf8')
    print('built',name)
if __name__=='__main__':
    for n,c in PACKS.items():build(n,c)
