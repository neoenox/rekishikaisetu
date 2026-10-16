"""YouTube description draft for the ninja video (chapters from the real timeline + credits + references + pre-publish checklist) -> out/nj_description.md"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
tl=json.loads((ROOT/'data'/'nj_timeline.json').read_text(encoding='utf8'))
def ts(s):s=int(s);return f'{s//60}:{s%60:02d}'
CH={'intro':'導入：黒装束・覆面・手裏剣のイメージはどこから？','shinobi':'「忍び」とは、何をした人たちか','books':'忍術書には、何が書かれているか','black':'黒装束と覆面は、どこから来たのか','shuriken':'手裏剣は、使われていたのか','image':'いまのイメージ','end':'結論：分かること、決められないこと'}
chapters=[f'{ts(c["start"])} {CH[c["key"]]}' for c in tl]
dur=tl[-1]['end'];total=f'{int(dur//60)}分{int(dur%60)}秒'
IMGS=json.loads((ROOT/'assets'/'ndl_ninja'/'manifest.json').read_text(encoding='utf8'))
used={'hokusai_black_ninja.jpg','hokusai_bar_shuriken.jpg','ehon_taikoki_kimura.jpg','honcho_nijushiko_yamamoto.jpg','toyokuni_goemon_hisayoshi.jpg','shoninki_ten_p1.jpg','shoninki_chi_p12.jpg','shoninki_jin_p21.jpg','fujita_flat_shuriken.jpg'}
TITLE={'hokusai_black_ninja.jpg':'葛飾北斎『北斎漫画』6編(1878年刊)','hokusai_bar_shuriken.jpg':'葛飾北斎『北斎漫画』6編(1878年刊)','ehon_taikoki_kimura.jpg':'岡田玉山『絵本太閤記』(1884年刊)','honcho_nijushiko_yamamoto.jpg':'『本朝廿四孝』上(明治期)','toyokuni_goemon_hisayoshi.jpg':'豊国『石川五右衛門・大願久吉』','shoninki_ten_p1.jpg':'名取正武『正忍記』天(寛保3年=1743年の写し)','shoninki_chi_p12.jpg':'名取正武『正忍記』地(寛保3年=1743年の写し)','shoninki_jin_p21.jpg':'名取正武『正忍記』人(寛保3年=1743年の写し)','fujita_flat_shuriken.jpg':'藤田西湖『忍術からスパイ戦へ』(1942年刊)'}
imglines=[f'・{TITLE[m["file"]]}:{m["source_url"]}' for m in IMGS if m['file'] in used]
L=['# YouTube 投稿用ドラフト：忍者は、黒装束で手裏剣を投げていたのか\n',
'## タイトル案',
'1. 忍者は、黒装束で手裏剣を投げていたのか？ 国立国会図書館の解説で確かめる',
'2. 「黒装束の忍者」は江戸の舞台から？ 忍術書と研究者の説明を確認',
'3. 忍者の黒装束と手裏剣、史料にはどう書かれている？\n',
'## 概要欄(そのまま貼り付け用)\n','```',
'忍者といえば、黒装束に覆面、そして手裏剣。そのイメージは、いつ、どこから来たのでしょうか。',
'この動画では、国立国会図書館の解説と、研究者の説明から、忍者の通説を確かめます。実際の「忍び」はどんな人たちだったのか、忍術書(『万川集海』『正忍記』『忍秘伝』)には何が書かれているのか、黒装束と覆面・手裏剣はどこから広まったのか。最後に、「分かること」と「決められないこと」を分けて考えます。',
'','■ チャプター']+chapters+[
'','■ 動画で確かめたこと(要点)',
'・黒装束と覆面を「忍者の決まった姿」として描く表現は、江戸時代の演劇(歌舞伎・浄瑠璃)から広まったと、国立国会図書館の解説や研究者が説明しています(18世紀中ごろとする説明は、三重大学が掲載した吉丸雄哉氏の記事)。',
'・『正忍記』には、茶色・柿色・黒色・紺色を着るとあります(国立国会図書館の解説による)。黒い服そのものが、なかったわけではありません。',
'・国立国会図書館の解説では、これまでに見つかっている忍術書に手裏剣の記述はなく、忍者が使った記録も見当たらないとされています。ただし、使った可能性は否定できないとも書かれています。',
'・「忍者」という呼び名が定着したのは昭和30年代とする説明があります(山田雄司氏)。ただし、1856年刊の『武用弁略』にも「忍者」の語が見えます。',
'','■ 参考資料(確認に使ったもの)',
'・国立国会図書館「本の万華鏡 第33回 NINJA 虚像(エンタメ)と実像(ホンモノ)」 弐之巻:https://www.ndl.go.jp/kaleido/entry/33/2.html 参之巻:https://www.ndl.go.jp/kaleido/entry/33/3.html 秘伝之巻:https://www.ndl.go.jp/kaleido/entry/33/4.html',
'・山田雄司「忍者の『誕生』」:https://www.igaportal.co.jp/ninja/1547',
'・吉丸雄哉氏の記事(三重大学 R-navi):https://www.mie-u.ac.jp/R-navi/column/cate006/YoshimaruKatsuya.html',
'','■ 出典・クレジット',
'・画像:国立国会図書館デジタルコレクション(インターネット公開・保護期間満了、パブリックドメインマーク)']+imglines+[
'・音声:VOICEVOX:四国めたん',
'・音楽:魔王魂(https://maou.audio/) ピアノ36 / ピアノ12 / ピアノ40(作曲:森田交一。音量調整・場面に合わせた切り替えを行っています)',
'・図・年表:自作',
'','■ 注意',
'・画像は、江戸時代から昭和期の絵・書物です。演劇の演出上の姿と、実際の忍びの姿は区別して紹介しています。',
'・忍術書の本文そのものではなく、国立国会図書館の解説と研究者の説明を紹介する形で構成しています。誤りがあればコメントでお知らせください。',
'・動画内には出典・クレジットを表記せず、この概要欄にまとめています。',
'','■ このチャンネルについて','寄り道ラボは、ふと気になったことを、資料やデータで調べる解説チャンネルです。',
'```\n',
'## タグ案','忍者, 黒装束, 手裏剣, 忍術書, 万川集海, 正忍記, 歴史, 日本史, 江戸時代, 歌舞伎, 雑学, 国立国会図書館, 検証, 思い込み\n',
'## 投稿前チェック(自分で確認が必要)',
'- [ ] **動画を通しで見る・聞く**(動き、ナレーションの読み、BGMの音量、画像の切り出しと説明の整合)',
'- [ ] **原文の確認(宿題)**:『正忍記』『万川集海』の本文(装束・手裏剣の記述の有無)、吉丸雄哉『忍者とは何か』第三部。詳しくは `docs/themes/20261016_ninja/08_fact_check.md`',
'- [ ] **画像の公開範囲を、画像ごとに確認**(`docs/themes/20261016_ninja/05_images_rights.md`)。特に『忍術からスパイ戦へ』(1942年刊・著者没1966年)',
'- [ ] 山田雄司氏の読み(やまだ・ゆうじ)・所属の確認',
'- [ ] 概要欄のURLが開けるか(上級者向け機能が有効になるまで、クリックできない)',
'- [ ] VOICEVOX:四国めたん / BGM(魔王魂 ピアノ36/12/40)の最新規約',
'- [ ] YouTubeの設問:**「改変・合成コンテンツ」「AIの使用」は、設問の公式基準に照らして確認**(生成画像は不使用、合成音声(VOICEVOX)は使用)。子ども向け=「いいえ」、リミックス=許可しない',
'- [ ] 字幕:`out/nj_subtitles.srt` をアップロード(日本語)',
'- [ ] サムネイルAを設定し、投稿後の表示(スマートフォンの小さな表示)を確認','']
(ROOT/'out'/'nj_description.md').write_text('\n'.join(L)+'\n',encoding='utf8');print('\n'.join(chapters),'\nduration',total)
