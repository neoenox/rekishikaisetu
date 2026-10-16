"""World-map video: build data/nj_scenes.json from the reviewed script (docs/themes/.../09_script_v2.md).
One scene per chapter; narration = the numbered lines (the 〔..〕 evidence tags are stripped). Pronunciations: data/nj_pronunciations.json (edit after the kana check)."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'docs'/'themes'/'20261016_ninja'/'09_script_v2.md'
KEYS=['intro','shinobi','books','black','shuriken','image','end']
def main():
    t=SRC.read_text(encoding='utf8');chs=re.split(r'\n## ',t)[1:];scenes=[]
    for c in chs:
        head=c.split('\n')[0]
        m=re.match(r'章(\d)　(.*)',head)
        if not m:continue
        n=int(m.group(1));lines=[re.sub(r'〔[^〕]*〕','',re.sub(r'^\d+\. ','',l)).strip() for l in c.split('\n') if re.match(r'^\d+\. ',l)]
        scenes.append(dict(id=n-1,key=KEYS[n-1],title=f'{m.group(2)}',category=f'忍者の通説を検証する｜章{n}',narration=''.join(lines)))
    (ROOT/'data'/'nj_scenes.json').write_text(json.dumps(scenes,ensure_ascii=False,indent=1),encoding='utf8')
    pr=ROOT/'data'/'nj_pronunciations.json'
    if not pr.exists():pr.write_text('{}',encoding='utf8')
    print(len(scenes),'scenes',sum(len(s['narration']) for s in scenes),'chars')
if __name__=='__main__':main()
