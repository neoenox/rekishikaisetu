"""Display text for subtitles: spoken script uses kanji numerals (reads reliably in VOICEVOX); on screen, quantities become Arabic numerals."""
import re
D={'〇':0,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
NUM='〇一二三四五六七八九十百千'
def k2i(s):
    """kanji numeral below 10000 -> int (十百千 positional)"""
    total=0;cur=0
    for ch in s:
        if ch in D:cur=cur*10+D[ch] if False else D[ch]
        elif ch=='十':total+=(cur or 1)*10;cur=0
        elif ch=='百':total+=(cur or 1)*100;cur=0
        elif ch=='千':total+=(cur or 1)*1000;cur=0
    return total+cur
def big(s):
    """e.g. 一万三千 / 二万 / 千五百八十二 -> text"""
    if len(s)>1 and all(c in D for c in s):return ''.join(str(D[c]) for c in s)   # positional digits (年号: 一五六九 -> 1569)
    if '万' in s:
        a,b=s.split('万',1);n=(k2i(a) if a else 1)*10000+(k2i(b) if b else 0)
    else:n=k2i(s)
    if n>=10000 and n%10000==0:return f'{n//10000}万'
    if n>10000 and n%1000==0:return f'{n//10000}万{(n%10000)//1000}千'
    return str(n)
COUNTERS='年月日人時間分時歳メートルキロメートルキロ半'
def display(t):
    t=t.replace('二十、三十人','20〜30人').replace('百五十、六十人','150〜160人').replace('二十人から三十人','20〜30人').replace('百五十人から百六十人','150〜160人')
    # decimal: 十七点五キロ / 一点五キロ
    t=re.sub(r'([%s]+)・([〇一二三四五六七八九]+)(?=倍)'%NUM,lambda m:f'{big(m.group(1))}.{"".join(str(D[c]) for c in m.group(2))}',t)  # 一・四倍 -> 1.4倍
    t=re.sub(r'([%s]+)点([〇一二三四五六七八九]+)'%NUM,lambda m:f'{big(m.group(1))}.{"".join(str(D[c]) for c in m.group(2))}',t)
    # maximal numeral run -> arabic when it is a quantity (followed by a counter, or containing 万)
    def conv(m):
        s=m.group(0);nxt=t_[m.end():m.end()+4]
        if s=='万':return s   # bare 万 inside a word (万能, 数万人) is not a quantity
        if '万' in s or re.match(r'(年|月|日|人|歳|分|メートル|キロ|時間|時|度|倍|巻|世紀)',nxt):return big(s)
        return s
    t_=t
    t=re.sub('[%s万]+'%NUM,conv,t)
    return t
if __name__=='__main__':
    import json,sys
    for x in ['天正十年六月二日の未明','千五百八十二年のことです。','少ない説で二十、三十人、多い説で百五十、六十人。','光秀の兵は、約一万三千ともいわれます。','約十七点五キロメートルでした。','五キロなら約三時間半、四キロなら約四時間二十分、三キロなら約五時間五十分かかります。','一つは、怨恨説。二つ目は、野望説。四国と三職推任と三男。','約百十メートルです。約二百三十メートル。約百二十メートル四方。','二万、三万とする説もあります。','千五百九十一年から翌年にかけて','十一日後、六月十三日','土佐一国と阿波の南の二郡以外を','約一点五キロメートル','約八百メートルの距離です']:print(display(x))
