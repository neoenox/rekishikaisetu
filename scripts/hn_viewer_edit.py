"""Non-destructive viewer edit: readable map notes, source graphics, theory comparisons.

Uses the existing final video's first half and the full-length original audio.
python scripts/hn_viewer_edit.py prepare|render|verify
"""
from pathlib import Path
import json, math, subprocess, sys, re
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'cache' / 'viewer_edit'
OUT = ROOT / 'out' / 'viewer_edit'
WORK.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
TL = json.loads((ROOT/'data/hn_timeline.json').read_text(encoding='utf8'))
VIS = json.loads((ROOT/'data/hn_scene_visuals.json').read_text(encoding='utf8'))['scenes']
AUDIO = json.loads((ROOT/'out/hn_audio_report.json').read_text(encoding='utf8'))
SEG = AUDIO['segments']
CUT = next(s['start'] for s in TL if s['key']=='s_intro')
TOTAL = math.ceil(AUDIO['total_seconds']) + 2
BG = '#0b171f'; PANEL = '#132630'; INK = '#f2eee3'
GOLD = '#e8c783'; DIM = '#b4c3c8'; BLUE = '#8bbac9'; RED = '#dfab9a'
FONT_DIR = Path('C:/Windows/Fonts')
FONTS = {}
MEASURE = ImageDraw.Draw(Image.new('RGB',(1,1)))
CHECKS = []

def font(size, serif=False):
    key = size, serif
    if key not in FONTS:
        f = ImageFont.truetype(str(FONT_DIR/('NotoSerifJP-VF.ttf' if serif else 'NotoSansJP-VF.ttf')),size)
        f.set_variation_by_axes([750 if serif else 550])
        FONTS[key] = f
    return FONTS[key]

def wrap(text, size, width, serif=False):
    lines=[]; line=''; f=font(size,serif)
    for c in text:
        if c=='\n': lines.append(line);line='';continue
        if line and MEASURE.textlength(line+c,font=f)>width:
            if c in '、。，）」』':
                tail=line[-1];line=line[:-1];lines.append(line);line=tail+c
            else:lines.append(line);line=c
        else:line+=c
    if line:lines.append(line)
    return lines

def text(d,xy,content,size=38,fill=INK,width=1750,serif=False,max_lines=None):
    lines=wrap(content,size,width,serif)
    if max_lines is not None:
        assert len(lines)<=max_lines,(content,len(lines),max_lines)
    x,y=xy
    for line in lines:
        box=d.textbbox((x,y),line,font=font(size,serif))
        assert box[2]<=1900 and box[3]<=1060,(content,box)
        d.text((x,y),line,font=font(size,serif),fill=fill)
        y+=int(size*1.5)
    CHECKS.append({'text':content,'size':size,'lines':len(lines)})
    return y

def section(key):
    if key=='hook':return '序章',0
    for prefix,title,n in [('a_','光秀の歩み',1),('b_','1582年の情勢',2),('c_','変の直前',3),('d_','京都への道',4),('f_','各地の動き',5),('s_','史料を読む',6),('m_','動機を比べる',7),('e_','分かること・謎',8)]:
        if key.startswith(prefix):return title,n
    return '歴史の補足',5

def title(sc):return re.sub(r'^\d+ / ','',sc['title']).replace('豆知識 / ','')
def scene_segments(sc):return [s for s in SEG if s['scene']==sc['id']]

# Short on-screen notes follow the narration; do not add new historical claims.
MAP_NOTES = {
 'a_origin':[('生年も、出自も諸説',1),('美濃・明智城の出身とする説',2),('信長に仕える前は謎が多い',4)],
 'a_retainer':[('1568年　義昭の上洛に参加',1),('坂本を拠点に、信長の重臣へ',3),('主従関係が変わる時期は諸説',6)],
 'a_tanba':[('1579年　丹波を平定',2),('亀山城が、のちの出発点に',3),('近畿で大きな力を持つ立場へ',5)],
 'b_peak':[('武田氏が滅び、勢力を拡大',1),('信忠への権力移譲が進む',2),('高い官職への就任話も浮上',4)],
 'b_west':[('備中の秀吉が援軍を求める',1),('四国政策の転換で交渉が難航',2),('光秀は元親との取次を担う',3)],
 'c_ieyasu':[('安土で、家康の接待を担当',1),('信長から、先陣の命令',3),('接待役が交代した理由は不明',5)],
 'c_atago':[('亀山城から、愛宕山へ',1),('連歌の発句「ときは今…」',3),('謀反の意思を示すかは諸説',4)],
 'c_nobunaga':[('5月29日　少人数で本能寺へ',0),('6月1日　公家や僧侶が来訪',2),('信忠も訪れたと伝わる',3)],
 'f_intro':[('西：秀吉は備中、信孝は大坂',4),('北：勝家らは上杉方と対峙',6),('家康は堺からの帰路へ',7)],
 'f_ieyasu':[('京へ向かう途中、変を知る',1),('伊賀・伊勢を経て三河へ',4),('同行者や経路の詳細には諸説',6)],
 'f_hideyoshi':[('備中高松城で毛利方と対峙',0),('6月3日夜〜4日未明に変報',3),('信長の死を隠し、和睦を急ぐ',5)],
 'f_north':[('柴田勝家らは魚津城を攻撃',1),('6月3日　魚津城が落城',2),('変報を受けた日時は不明',7)],
}

# Each source has a stable identity and three reading questions.
SOURCES = {
 's_koki':('信長公記','太田牛一｜信長の側近','1610年の奥書をもつ写本',[
   ('どんな記録？','年月日を追って、信長の事績を記す',1),
   ('何が分かる？','事件の経緯をたどる基礎になる',3),
   ('読むときの注意','他の史料との照合が必要',6)]),
 's_kanemi':('兼見卿記','吉田兼見｜京都・吉田神社','変の前後を記した日記',[
   ('どんな記録？','光秀と交流のあった人物の日記',1),
   ('何が分かる？','変のあとも、光秀との往来がある',2),
   ('読むときの注意','天正10年分の別本・書き換えが論点',4)]),
 's_nikki':('公家と僧の日記','多聞院日記・言経卿記','その場の見聞を伝える記録',[
   ('多聞院日記','興福寺の僧たちが書き継いだ日記',1),
   ('言経卿記','公家・山科言経が記した日記',4),
   ('読むときの注意','書き手の立場や伝聞にも目を向ける',7)]),
 's_frois':('フロイス「日本史」','ルイス・フロイス｜宣教師','西洋のキリスト教徒の視点',[
   ('どんな記録？','宣教師が日本での活動を記す',1),
   ('何が分かる？','他の史料にない記述や、動機への言及',4),
   ('読むときの注意','宣教師の立場を踏まえて読む',7)]),
 's_koretou':('惟任退治記','大村由己｜秀吉の側近','1582年、変の直後に成立',[
   ('どんな記録？','変から山崎の戦い、信長の葬儀まで',1),
   ('何が分かる？','秀吉側が、事件をどう描いたか',3),
   ('読むときの注意','秀吉の偉大さを強調する記述',5)]),
 's_kawasumi':('川角太閤記','川角三郎右衛門｜田中吉政の家臣','1620年代に成立したとされる',[
   ('どんな記録？','武士たちから集めた聞き書き',1),
   ('何が分かる？','光秀の元家臣の話も含まれる',3),
   ('読むときの注意','年月日を追う記録とは性格が違う',6)]),
 's_akechi':('明智軍記','作者不明｜光秀を描く軍記物','変から約100年後に成立',[
   ('どんな記録？','光秀を主人公にした軍記物',0),
   ('何が分かる？','後世に伝わった光秀の人物像',2),
   ('読むときの注意','史実と創作が混ざる。慎重な検討が必要',3)]),
 's_tokudai':('当代記','編者は不詳｜江戸初期の史書','寛永のころに成立',[
   ('どんな記録？','先行する記録を再編した二次史料',1),
   ('何が分かる？','江戸初期にまとめられた出来事の記録',2),
   ('読むときの注意','小瀬甫庵「信長記」の影響に注意',4)]),
}
THEORIES = {
 'm_onkon':('怨恨説','信長への恨み・不満が\n引き金になった',('後世の逸話','「三つの遺恨」など',3),('史実かどうか','後世の書物に頼る部分が多い',4)),
 'm_yabou':('野望説','光秀自身が\n天下を狙った',('記述と解釈','太田牛一・フロイスの記述など',3),('内心は分からない','野心の推測や連歌の解釈に異論',4)),
 'm_totsupatsu':('突発説','目の前の好機を見て\n突発的に決起した',('少人数の信長','変後の行動や、手薄な供回り',2),('野望説との関係','野望説から派生した説とされる',5)),
 'm_chotei':('朝廷関与説','朝廷が、光秀の\n背後にいた',('朝廷との関係','暦・譲位・三職推任、日記の欠落',3),('命令の証拠','綸旨や、光秀の勅命の主張がない',4)),
 'm_yoshiaki':('足利義昭黒幕説','義昭が、光秀を\n動かした',('変のあとの書状','6月12日付・13日付の文言を解釈',3),('直接証拠の不足','積極的関与を直接示す証拠はない',4)),
 'm_shikoku':('四国説','四国政策の転換で\n立場が揺らいだ',('新たな書状','元親から利三へ。石谷家文書',2),('動機との結びつき','書状の存在だけでは断定できない',6)),
 'm_hido':('信長非道阻止説','信長の行いを\n止めようとした',('信長の行動への評価','信長の「非道」を動機とみる',2),('前提への異論','仮定を重ねているとの批判',3)),
 'm_kuro':('その他の黒幕説','秀吉・家康・\nイエズス会など',('推理や風説','利益を得た者への疑いなど',2),('裏付けが乏しい','史料に基づく研究と区別して考える',5)),
}

def active_index(rows, segs, t):
    return max([i for i,r in enumerate(rows) if segs[min(r[-1],len(segs)-1)]['start']<=t] or [0])

def base(sc):
    im=Image.new('RGB',(1920,1080),BG);d=ImageDraw.Draw(im)
    # Fine editorial rules, rather than the old repeated terrain background.
    d.line((70,142,1850,142),fill='#36454b',width=2)
    name,n=section(sc['key'])
    text(d,(72,34),name,30,GOLD)
    text(d,(390,26),title(sc),46,INK,width=1450,max_lines=1)
    text(d,(72,1026),'本能寺の変 1582',22,DIM)
    return im,d

def reading_cards(d, rows, segs,t,x=850,y=220,width=990):
    current=active_index(rows,segs,t)
    for i,(lab,body,at) in enumerate(rows):
        yy=y+i*196;on=i==current
        d.rounded_rectangle((x,yy,x+width,yy+174),14,fill=PANEL if on else '#101f28',outline=GOLD if on else '#32454e',width=3 if on else 1)
        text(d,(x+28,yy+16),lab,29,GOLD if on else DIM)
        text(d,(x+28,yy+66),body,40,INK,width=width-58,max_lines=2)

def source_slide(sc,t):
    im,d=base(sc);name,author,when,rows=SOURCES[sc['key']];ss=scene_segments(sc)
    text(d,(74,188),'記録を読む',27,GOLD)
    text(d,(74,244),name,66,INK,width=720,serif=True,max_lines=2)
    text(d,(78,462),author,30,DIM,width=680,max_lines=2)
    d.line((80,588,742,588),fill=GOLD,width=3)
    text(d,(78,620),'書かれた時期・立場',28,GOLD)
    text(d,(78,680),when,39,INK,width=660,max_lines=2)
    reading_cards(d,rows,ss,t)
    return im

def theory_slide(sc,t):
    im,d=base(sc);key=sc['key'];name,claim,evidence,weakness=THEORIES[key];ss=scene_segments(sc)
    ix=list(THEORIES).index(key)
    for i,k in enumerate(THEORIES):
        x=74+i*222;on=i==ix
        d.rectangle((x,165,x+200,171),fill=GOLD if on else '#354852')
        text(d,(x,179),['怨恨','野望','突発','朝廷','義昭','四国','非道阻止','その他'][i],26,GOLD if on else DIM)
    text(d,(76,272),'この説の主張',29,GOLD)
    text(d,(76,335),claim,57,INK,width=730,serif=True,max_lines=3)
    text(d,(76,687),'どの説にも、決め手はない',30,DIM,width=720,max_lines=1)
    rows=[('根拠として挙げられること',evidence[0]+'\n'+evidence[1],evidence[2]),('弱点・残る疑問',weakness[0]+'\n'+weakness[1],weakness[2])]
    current=active_index(rows,ss,t)
    for i,(lab,body,at) in enumerate(rows):
        yy=280+i*248;col=BLUE if i==0 else RED;on=current==i
        d.rounded_rectangle((870,yy,1846,yy+220),14,fill=PANEL,outline=col if on else '#354852',width=3 if on else 1)
        text(d,(900,yy+18),lab,28,col)
        parts=body.split('\n')
        text(d,(900,yy+70),parts[0],43,INK,width=910,max_lines=1)
        text(d,(900,yy+142),parts[1],34,DIM,width=910,max_lines=2)
    return im

def overview_slide(sc,t):
    im,d=base(sc);key=sc['key'];ss=scene_segments(sc)
    if key in ('s_intro','s_later'):
        text(d,(78,186),'史料は、時期と立場をセットで読む',61,INK,serif=True,max_lines=1)
        cols=[('変のころ','日記・直後の記録','兼見卿記／惟任退治記'),('数十年後','聞き書き・編纂された記録','川角太閤記／当代記'),('約100年後','後世の軍記物','明智軍記')]
        d.line((200,410,1700,410),fill=GOLD,width=4)
        for i,(when,kind,examples) in enumerate(cols):
            x=80+i*610;d.ellipse((x+20,396,x+48,424),fill=GOLD)
            text(d,(x,300),when,45,GOLD,width=560,max_lines=1)
            text(d,(x,472),kind,36,INK,width=540,max_lines=2)
            text(d,(x,604),examples,30,DIM,width=540,max_lines=2)
        text(d,(80,752),'古い記録ほど、無条件に正しいわけではない。',36,GOLD,max_lines=1)
    elif key=='m_compare':
        text(d,(78,188),'説を比べると、残る疑問が見える',58,INK,serif=True,max_lines=1)
        rows=[('怨恨説','後世の逸話を、どこまで史実とみるか',2),('野望説','本人の内心を、どう確かめるか',2),('朝廷・義昭説','決定的な文書があるか',3),('四国説','書状を、決起の動機にどう結びつけるか',4)]
        cur=active_index(rows,ss,t)
        for i,(lab,body,_) in enumerate(rows):
            y=310+i*114
            if i==cur:d.rounded_rectangle((76,y-6,1844,y+94),10,fill=PANEL)
            text(d,(102,y+7),lab,39,GOLD,width=350,max_lines=1)
            text(d,(490,y+7),body,39,INK,width=1300,max_lines=1)
        text(d,(100,785),'史料の少なさに加え、同じ史料から異なる解釈が生まれる。',32,DIM,max_lines=1)
    elif key=='m_intro':
        text(d,(90,224),'光秀は、なぜ討ったのか。',76,INK,serif=True,max_lines=1)
        text(d,(94,381),'現在も、定説はありません。',53,GOLD,max_lines=1)
        for x,head,body in [(96,'主張','何が動機だったと考えるか'),(706,'根拠','どの史料・状況を挙げるか'),(1316,'弱点','何がまだ説明できないか')]:
            d.line((x,546,x+490,546),fill=GOLD,width=3)
            text(d,(x,573),head,44,INK)
            text(d,(x,662),body,34,DIM,width=480,max_lines=2)
    elif key=='e_end':
        text(d,(80,186),'地形で分かること。史料にも残る謎。',61,INK,serif=True,max_lines=1)
        rows=[('移動の条件','現代の道路に沿った参考経路：約20.7km',1),('事件の経緯','光秀の立場、信長・信忠の死、各地の動き',4),('なお残る謎','動機と、信長の最期の細部は確定しない',5)]
        reading_cards(d,rows,ss,t,x=80,y=300,width=1760)
    else:
        spec=VIS[key].get('trivia',{})
        head=spec.get('headline',title(sc))
        text(d,(80,200),head,66,INK,width=1740,serif=True,max_lines=2)
        if key=='tr_teki':rows=[('有名な言葉','「敵は本能寺にあり」',1),('史料から見ると','同時代の史料に、本人の発言の記録はない',2),('後世との区別','江戸時代の書物で広まった俗説とされる',3)]
        else:rows=[('後年の回想','本城惣右衛門が約58年後に書いた覚書',1),('証言の趣旨','「家康様だとばかり思っていた」',2),('読むときの注意','一人の回想を、軍全体の認識には広げられない',4)]
        reading_cards(d,rows,ss,t,x=80,y=320,width=1760)
    return im

def stamp(v):
    cs=round(v*100);return f'{cs//360000}:{cs//6000%60:02}:{cs//100%60:02}.{cs%100:02}'
def acol(hex):return '&H'+hex[5:7]+hex[3:5]+hex[1:3]+'&'
ASS_HEAD='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Noto Sans JP,40,&H00F2EEE3,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''

def event(events,a,b,payload,layer=1):
    if b>a:events.append(f'Dialogue: {layer},{stamp(a)},{stamp(b)},Default,,0,0,0,,{payload}')
def rect(events,a,b,box,col,layer=0):
    x,y,x1,y1=box
    event(events,a,b,r'{\an7\pos(0,0)\p1\c'+acol(col)+r'}'+f'm {x} {y} l {x1} {y} {x1} {y1} {x} {y1}',layer)
def ass_text(events,a,b,x,y,content,size=38,col=INK,width=1700,serif=False):
    lines=wrap(content,size,width,serif)
    assert len(lines)<=3,(content,lines)
    # libass may resolve the variable Noto font to its lightest master on Windows.
    # Use the installed static Japanese family for burned-in overlays.
    f='Yu Mincho' if serif else 'Yu Gothic'
    for i,line in enumerate(lines):
        event(events,a,b,r'{\an7\pos('+f'{x},{y+i*int(size*1.5)}'+r')\fn'+f+r'\b700\fs'+str(size)+r'\c'+acol(col)+r'}'+line)

def prepare():
    # Prefix: preserve the existing motion and illustrations, replace dense notes.
    events=[]
    for sc in TL:
        a,b=sc['start'],min(sc['end'],CUT);key=sc['key']
        if a>=CUT:break
        if key=='hook':a=22.6
        rect(events,a,b,(0,0,1920,151),BG)
        name,n=section(key)
        ass_text(events,a,b,50,16,name,26,GOLD)
        ass_text(events,a,b,50,55,title(sc),51,INK,width=1320,serif=True)
        date=VIS[key].get('date','')
        ass_text(events,a,b,1400,22,date,31,GOLD,width=480)
        note='現代の地図による位置図' if VIS[key].get('map') else '現代の地形｜高さ2倍｜軍勢は模式表現'
        ass_text(events,a,b,1190,108,note,24,DIM,width=680)
        if key not in MAP_NOTES:continue
        ss=scene_segments(sc);rows=MAP_NOTES[key]
        points={sc['start'],b}
        for _,idx in rows:points.add(ss[min(idx,len(ss)-1)]['start'])
        hidden=[]
        for _,sa,sb in VIS[key].get('images',[]):hidden.append((ss[sa]['start'],ss[sb]['end']));points.update(hidden[-1])
        pts=sorted(p for p in points if a<=p<=b)
        for start,end in zip(pts,pts[1:]):
            if any(ha<=start<hb for ha,hb in hidden):continue
            rect(events,start,end,(45,170,912,805),BG)
            ass_text(events,start,end,76,198,'ここで押さえること',27,GOLD,width=790)
            cur=active_index([(None,body,idx) for body,idx in rows],ss,start+.01)
            for j,(body,idx) in enumerate(rows):
                y=286+j*149
                if j==cur:rect(events,start,end,(73,y-10,80,y+108),GOLD)
                ass_text(events,start,end,105,y,body,41,INK if j==cur else DIM,width=745)
            ass_text(events,start,end,80,752,'細部に諸説あり。地図は概略位置。',25,DIM,width=790)
    (WORK/'prefix.ass').write_text(ASS_HEAD+'\n'.join(events),encoding='utf-8-sig')
    # Back half: image changes are tied to sentences, with no empty reveal states.
    states=[]; manifest=[]
    for sc in TL:
        if sc['start']<CUT:continue
        ss=scene_segments(sc)
        bounds=[sc['start']]+[s['start'] for s in ss if s['start']>sc['start']]+[sc['end']]
        for j,(a,b) in enumerate(zip(bounds,bounds[1:])):
            if b-a<.005:continue
            if sc['key'] in SOURCES:im=source_slide(sc,a+.01)
            elif sc['key'] in THEORIES:im=theory_slide(sc,a+.01)
            else:im=overview_slide(sc,a+.01)
            path=WORK/f'{sc["key"]}_{j:02}.png';im.save(path)
            states.append((path,a,b));manifest.append({'scene':sc['key'],'start':a,'end':b,'image':str(path)})
    # Explicit final still and duration ensure the last frame is held through the tail.
    states[-1]=(states[-1][0],states[-1][1],TOTAL)
    concat=[]
    for path,a,b in states:concat.extend([f"file '{path.as_posix()}'",f'duration {b-a:.9f}'])
    concat.append(f"file '{states[-1][0].as_posix()}'")
    (WORK/'slides.ffconcat').write_text('\n'.join(concat)+'\n',encoding='utf8')
    from hn_text import display
    events=[]
    # The subtitle band and chapter progress are outside all infographic content.
    rect(events,0,TOTAL-CUT,(0,888,1920,1016),BG)
    for seg in SEG:
        if seg['start']<CUT:continue
        a,b=seg['start']-CUT,seg['end']-CUT
        shown=display(seg['text']);size=44
        while len(wrap(shown,size,1740))>2:size-=2
        assert size>=38
        ls=wrap(shown,size,1740)
        top=910 if len(ls)==1 else 890
        ass_text(events,a,b,90,top,shown,size,INK,width=1740)
    (WORK/'late.ass').write_text(ASS_HEAD+'\n'.join(events),encoding='utf-8-sig')
    (OUT/'layout_checks.json').write_text(json.dumps({'text_blocks':len(CHECKS),'minimum_body_px':34,'checks':CHECKS,'states':manifest},ensure_ascii=False,indent=2),encoding='utf8')
    # Contact sheet is generated from actual layout states for visual inspection.
    picked=[]
    for key in ['s_intro','s_koki','s_kanemi','s_nikki','s_later','m_intro','m_onkon','m_yabou','m_chotei','m_shikoku','m_compare','e_end']:
        chosen=[s for s in states if s[0].stem.startswith(key+'_')]
        picked.append(chosen[min(3,len(chosen)-1)][0])
    sheet=Image.new('RGB',(1920,1440),BG)
    for i,p in enumerate(picked):sheet.paste(Image.open(p).resize((640,360),Image.Resampling.LANCZOS),((i%3)*640,(i//3)*360))
    sheet.save(OUT/'design_overview.jpg',quality=92)
    print(json.dumps({'cut':CUT,'duration':TOTAL,'slides':len(states),'text_blocks':len(CHECKS)}),flush=True)

def run(args,logname):
    print(logname,flush=True)
    with (WORK/logname).open('w',encoding='utf8') as log:
        subprocess.run(['ffmpeg','-hide_banner','-nostats','-y']+args,stderr=log,stdout=log,check=True,cwd=WORK)

ENC=['-c:v','h264_nvenc','-preset','p5','-cq','20','-b:v','0','-pix_fmt','yuv420p','-r','30','-video_track_timescale','15360']
def render():
    # New named outputs; never overwrite the reviewed original or its caches.
    run(['-i',str(ROOT/'out/honnoji.mp4'),'-t',f'{CUT:.9f}','-an','-vf','ass=prefix.ass']+ENC+[str(WORK/'prefix.mp4')],'prefix_encode.log')
    run(['-f','concat','-safe','0','-i','slides.ffconcat','-t',f'{TOTAL-CUT:.9f}','-an','-vf','fps=30,ass=late.ass']+ENC+[str(WORK/'late.mp4')],'late_encode.log')
    (WORK/'video.ffconcat').write_text("file 'prefix.mp4'\nfile 'late.mp4'\n",encoding='utf8')
    mix=ROOT/'cache/hn_mix.wav'
    measured=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(mix),'-af','loudnorm=I=-15:TP=-1.5:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
    j=json.loads(re.search(r'\{[^{}]*"input_i"[^{}]*\}',measured.stderr,re.S).group())
    af=f"loudnorm=I=-15:TP=-1.5:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,apad,afade=t=out:st={TOTAL-2}:d=2"
    run(['-f','concat','-safe','0','-i','video.ffconcat','-i',str(mix),'-map','0:v:0','-map','1:a:0','-c:v','copy','-af',af,'-c:a','aac','-b:a','192k','-ar','48000','-t',str(TOTAL),'-movflags','+faststart',str(OUT/'honnoji_viewer_edit.mp4')],'final_mux.log')
    (OUT/'hn_subtitles.srt').write_bytes((ROOT/'out/hn_subtitles.srt').read_bytes())
    print(str(OUT/'honnoji_viewer_edit.mp4'),flush=True)

def verify():
    path=OUT/'honnoji_viewer_edit.mp4'
    r=subprocess.run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)],capture_output=True,text=True,check=True)
    probe=json.loads(r.stdout);v=next(x for x in probe['streams'] if x['codec_type']=='video');a=next(x for x in probe['streams'] if x['codec_type']=='audio')
    report={'duration':float(probe['format']['duration']),'last_speech_end':SEG[-1]['end'],'video_duration':float(v['duration']),'audio_duration':float(a['duration']),'resolution':[v['width'],v['height']],'fps':v['avg_frame_rate']}
    assert report['duration']>=SEG[-1]['end']+2,report
    assert abs(report['video_duration']-report['audio_duration'])<.12,report
    assert report['resolution']==[1920,1080] and report['fps']=='30/1'
    dec=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','null','-'],capture_output=True,text=True,check=True)
    assert not dec.stderr,dec.stderr
    report['full_decode']='PASS';report['tail_coverage']='PASS'
    (OUT/'media_verification.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report),flush=True)

if __name__=='__main__':{'prepare':prepare,'render':render,'verify':verify}[sys.argv[1]]()
