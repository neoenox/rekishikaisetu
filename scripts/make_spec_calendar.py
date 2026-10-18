"""Writes data/calendar_spec.json."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
spec=dict(slug='calendar',theme_dir='20261018_calendar',pack='09_calendar_meiji5',header_sub='明治5年の改暦を確かめる',images={k:dict(file=f'assets/calendar/art_{k}.png') for k in ('desk','moon','meiji','ledger','diary','flip')},
 bgm=[['intro','old','piano36'],['event','why','piano12'],['diary','end','piano40']],
 chapters=[
 dict(key='intro',title='十二月は、二日で終わった？',chapter_title='導入：十二月は、2日で終わった？',opener='十二月が、二日で終わった年',opener_until=1,scene=[
   dict(t='art',name='desk',box=[60,170,1860,850],at=0,dim=0.8,dir=1,note='イメージ（生成画像）。実際の場面の再現ではありません'),dict(t='shade',box=[60,170,1860,850],at=0,alpha=0.45),
   dict(t='chips',y=250,w=640,h=150,gap=160,size=56,items=[dict(at=1,text='明治5年12月2日'),dict(at=1,text='明治6年1月1日')]),
   dict(t='big',text='その次の日が、元日だった？',y=470,at=2,size=56,col='gold'),
   dict(t='panel',box=[120,580,1800,670],text='日が、消えてしまった？',at=3,size=44,hi=True),
   dict(t='panel',box=[120,690,1800,760],text='資料：国立国会図書館、国立天文台（暦Wiki・展示）',at=4,size=32)]),
 dict(key='old',title='当時の暦のしくみ',chapter_title='当時の暦は、どんなしくみだったのか',scene=[
   dict(t='art',name='moon',box=[60,170,1860,850],at=0,dim=0.8,dir=1,note='イメージ（生成画像）。実際の場面の再現ではありません'),dict(t='shade',box=[60,170,1860,850],at=0,alpha=0.62),
   dict(t='panel',box=[60,160,1860,250],text='当時の暦：太陰太陽暦',at=0,size=44,hi=True),
   dict(t='panel',box=[60,270,930,420],title='1か月',text='月の満ち欠けの周期（約29.5日）に合わせる。大の月30日・小の月29日',at=1,size=32),
   dict(t='panel',box=[990,270,1860,420],title='季節',text='地球が太陽をまわる周期（約365.25日）で移り変わる',at=2,size=32),
   dict(t='anim',name='lunar',box=[60,450,1860,730],at=3,s_cycle=3,s_leap=3),
   dict(t='panel',box=[60,740,1860,850],text='ずれを調節するため、2〜3年に1度、閏月を入れて13か月の年にした',at=3,size=38,col='gold')]),
 dict(key='event',title='明治五年に、何が起きたのか',chapter_title='明治5年に、何が起きたのか',scene=[
   dict(t='art',name='meiji',box=[60,170,1860,850],at=0,dim=0.8,dir=-1,note='イメージ（生成画像）。実際の場面の再現ではありません'),dict(t='shade',box=[60,170,1860,850],at=0,alpha=0.68),
   dict(t='panel',box=[60,170,1860,280],title='明治5年11月（旧暦）',text='政府が、太陽暦への改暦を発表（国立国会図書館）',at=0,until=4,size=36),
   dict(t='panel',box=[60,295,1860,405],title='11月9日の布告',text='旧暦の明治5年12月3日を、明治6年1月1日とする',at=1,until=4,size=40,hi=True),
   dict(t='panel',box=[60,420,1860,530],title='国立天文台 暦Wiki',text='わずか20日後に、1000年以上続いた暦をやめるのは、無謀な話だった',at=2,until=4,size=36),
   dict(t='panel',box=[60,545,1860,655],title='国立国会図書館',text='準備期間はほとんどなく、国内は混乱した',at=3,until=4,size=36),
   dict(t='anim',name='caltiles',box=[60,170,1860,530],at=4,s_a=4,s_b=5,s_c=6,s_skip=7),
   dict(t='panel',box=[60,540,1860,610],text='※旧暦のままなら12月3日にあたる日が、明治6年1月1日（12月3日は、実際には使われなかった）',at=7,size=30,col='dim'),
   dict(t='big',text='日が、消えたわけではない',y=640,at=8,size=56,col='gold'),
   dict(t='panel',box=[60,690,1860,760],text='続いている日の、数え方が切り替わった',at=9,size=40),
   dict(t='panel',box=[60,770,1860,840],text='明治5年の12月は、1日と2日の、2日間だけ',at=10,size=44,hi=True)]),
 dict(key='why',title='なぜ、暦を変えたのか',chapter_title='なぜ、暦を変えたのか',scene=[
   dict(t='art',name='ledger',box=[60,170,1860,850],at=0,dim=0.8,dir=1,note='イメージ（生成画像）。実際の場面の再現ではありません'),dict(t='shade',box=[60,170,1860,850],at=0,alpha=0.7),
   dict(t='panel',box=[60,170,1860,270],text='「給与の節約のためだった」という説明がある',at=1,until=3,size=44,col='gold'),
   dict(t='panel',box=[60,180,1860,300],title='国立国会図書館',text='西洋の制度を取り入れて近代化を進め、暦も、欧米と統一をはかった',at=3,until=9,size=36),
   dict(t='panel',box=[60,315,1860,435],title='国立天文台の解説',text='もう一つの背景：閏月と、月給',at=4,until=9,size=40),
   dict(t='panel',box=[60,450,1860,520],text='暦Wiki：財政上の理由は『大隈伯昔日譚』に記されていると紹介',at=5,until=9,size=32,col='dim'),
   dict(t='panel',box=[60,535,1860,685],title='国立天文台の解説',text='従来の暦を続ければ、明治6年は13か月。月給制の政府は、1か月分多く給料を払う計算',at=6,until=9,size=34),
   dict(t='panel',box=[60,700,1860,830],title='暦Wiki',text='2日間だけの12月の給料も払わず、合わせて2か月分を節約したと述べる',at=8,until=9,size=36),
   dict(t='panel',box=[60,200,1860,400],text='欧米との統一と、財政と、どちらがどれだけ大きかったのかは、これらの解説だけでは決められない',at=9,size=46,hi=True,col='gold')]),
 dict(key='diary',title='当日の日記',chapter_title='当日の日記を見てみる',scene=[
   dict(t='art',name='diary',box=[60,170,1860,850],at=0,dim=0.8,dir=-1,note='イメージ（生成画像）。実際の場面の再現ではありません'),dict(t='shade',box=[60,170,1860,850],at=0,alpha=0.7),
   dict(t='panel',box=[60,170,1860,290],title='国立国会図書館「当日の日記」',text='宍戸璣の日記（明治5年12月2日・3日）',at=0,size=40),
   dict(t='panel',box=[60,320,1860,460],title='12月2日（同館掲載の訳）',text='「太陰暦、この日をもって結尾とす」',at=2,size=44,col='gold',hi=True),
   dict(t='panel',box=[60,480,1860,550],text='※ここでの太陰暦は、当時使われていた暦',at=3,size=32,col='dim'),
   dict(t='panel',box=[60,570,1860,730],title='12月3日（同館掲載の訳）',text='「この日、初めて太陽歴日を用う、すなわち、癸酉、一月一日とす」',at=4,size=40,col='gold',hi=True),
   dict(t='panel',box=[60,750,1860,830],text='切り替わった日を、はっきり意識して書いている',at=6,size=40)]),
 dict(key='after',title='改暦の、その後',chapter_title='改暦の、その後',scene=[
   dict(t='art',name='flip',box=[60,170,1860,850],at=0,dim=0.8,dir=1,note='イメージ（生成画像）。実際の場面の再現ではありません'),dict(t='shade',box=[60,170,1860,850],at=0,alpha=0.7),
   dict(t='panel',box=[60,170,1860,300],title='国立国会図書館',text='福沢諭吉などの学者が、合理的な太陽暦を支持し、普及のための書物を著した',at=0,size=38),
   dict(t='panel',box=[60,320,1860,470],title='暦Wiki',text='太陽暦は、季節とのずれが少なく、閏年の決まりも単純。諸外国と同じ暦のほうが便利',at=1,size=38),
   dict(t='panel',box=[60,490,1860,610],title='暦Wiki',text='旧暦の併記は、明治42年の暦まで続けられた',at=2,size=40,hi=True),
   dict(t='panel',box=[60,630,1860,760],title='暦Wiki',text='会計年度：10月〜9月 → 1月〜12月に改められた',at=3,size=40)]),
 dict(key='end',title='分かること、決められないこと',chapter_title='結論：分かること、決められないこと',scene=[
   dict(t='cols2',size=34,xm=940,xm2=980,left=dict(title='分かること',title_at=0,items=[
      dict(at=1,text='明治5年12月3日が、明治6年1月1日に。12月は2日間だけ'),dict(at=3,text='日が消えたのではなく、日付の数え方が切り替わった'),dict(at=4,text='欧米との統一のほか、閏月と月給にまつわる財政の事情が、背景として挙げられている')]),
     right=dict(title='決められないこと',title_at=5,items=[
      dict(at=6,text='欧米との統一と財政の、どちらが決め手だったか'),dict(at=7,text='暮らしの、地域ごとの混乱の様子（この動画では未確認）')]))])
 ],
 desc=dict(title_main='明治5年は、12月が2日で終わったのか',title_no=1,
  titles=['明治5年は、12月が2日で終わった？ 国立国会図書館と国立天文台で確かめる','12月2日の次の日が元日？ 明治の改暦で、日は消えたのか','なぜ明治政府は、急に暦を変えたのか？ 閏月と月給の話を確かめる'],
  intro='日本には、12月が2日で終わった年がある。明治5年12月2日の次の日は、明治6年1月1日だった。本当に12月は2日しかなかったのか、日が消えてしまったのか。この動画では、国立国会図書館と国立天文台の解説から、明治の改暦で何が起きたのかを確かめます。太陰太陽暦のしくみ、改暦の経緯、当日の日記、なぜ暦を変えたのか(欧米との統一、閏月と月給)、改暦のその後を、分かることと決められないことを分けて見ていきます。',
  points=['明治5年(1872)11月9日の布告で、旧暦の明治5年12月3日を明治6年1月1日とし、太陽暦を採用しました(国立天文台 暦Wiki、国立国会図書館)。','12月2日は西暦1872年12月31日、その翌日が1873年1月1日(明治6年1月1日)です。日が消えたのではなく、日付の数え方が切り替わり、明治5年の12月は1日と2日の2日間だけになりました(国立国会図書館の日記の紹介、暦Wiki。対応表は自作)。','国立国会図書館は、欧米との統一をはかったと説明し、国立天文台の解説は、閏月と月給(明治6年が13か月になり1か月分多く給料が必要になる)を背景に挙げています。暦Wikiは、2日間だけの12月の給料も払わず、合わせて2か月分を節約したと述べています。ただし、どれがどれだけ大きな理由だったかは、これらの解説だけでは決められません。','宍戸璣の日記(国立国会図書館掲載の訳)に、12月2日「太陰暦、この日をもって結尾とす」、12月3日「この日、初めて太陽歴日を用う、すなわち、癸酉、一月一日とす」とあります。','旧暦の併記は明治42年の暦まで続けられ、会計年度も改められました(暦Wiki)。'],
  refs=['国立国会図書館「江戸から明治の改暦」:https://www.ndl.go.jp/koyomi/chapter1/s2.html','国立国会図書館「暦の渡来と普及」:https://www.ndl.go.jp/koyomi/chapter1/s1.html','国立国会図書館「当日の日記」(宍戸璣、明治5年12月2日):https://www.ndl.go.jp/nikki/citeid/shishido_18721202','国立天文台 暦計算室 暦Wiki「6. 明治維新と太陽暦」:https://eco.mtk.nao.ac.jp/koyomi/wiki/CEF2BBCB2FC6FCCBDCA4CECEF12F6.CCC0BCA3B0DDBFB7A4C8C2C0CDDBCEF1.html','国立天文台 貴重資料展示室 第14回展示「江戸から現在まで」:https://eco.mtk.nao.ac.jp/koyomi/exhibition/014/'],
  credit_lines=['・図・表・年表:自作(旧暦・新暦の対応表は、国立国会図書館の日記の紹介の日付を基にした自作です。外部画像は使用していません)','・サムネイルの背景と場面のイラスト:Codex(OpenAI)による生成イラスト(実際の場面の再現ではありません。明治初期の暦のイメージ。史実の再現ではありません)'],
  notes=['給与の節約など、改暦の理由については、国立天文台の解説・暦Wikiの記述を紹介したもので、どの理由がどれだけ大きかったかは、決められません。','「同館掲載の訳」は国立国会図書館のサイトに掲載された現代語訳で、日記の原文そのものではありません。','暮らしの、地域ごとの混乱の様子は、確認していません。','誤りがあればコメントでお知らせください。確認のうえ、訂正します。'],
  tags='明治5年, 改暦, 太陽暦, 旧暦, 12月2日, 明治時代, 日本史, 暦, 国立国会図書館, 国立天文台, 雑学, 検証',
  checks=['布告(太政官布告第337号)の原本画像の確認(任意。動画は国立天文台・国立国会図書館の記述に基づく)','「二十日ほど」の日数(暦Wiki)と、旧暦11月の日数の確認(任意)']),
 thumb=dict(bg='assets/calendar/thumb_art.png',lines=[['12月が',90,'white'],['2日で',110,'white'],['終わった？',140,'gold']],sub='明治5年の改暦を確かめる',y0=14,bar_y=520,bar_w=620,sub_size=44,shade_x=700,shade_w=520))
(R/'data'/'calendar_spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=1),encoding='utf8');print('spec written')
