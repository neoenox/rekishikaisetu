# 共通の制作ライン `scripts/vp.py`（Codex版の手順）

2026-10-17。それまでChatGPTに頼んでいた作業を、**Codex（`codex exec`、読み取り専用）に置き換えた**。動画ごとのスクリプトを、データ駆動の共通ラインにまとめた。

## 役割分担（ChatGPT → Codex）
| 作業 | 以前 | 今 |
|---|---|---|
| テーマの候補出し（10案） | ChatGPT | **Codex**（`docs/themes/20261017_batch2/03_prompt_codex.md` の指示文） |
| 台本の査読 | ChatGPT（ユーザーが貼る） | **Codex**：`python scripts/codex_review.py <テーマ> script` → `12_codex_script_review.md` |
| 完成動画（静止画・概要欄）の査読 | ChatGPT | **Codex**：`python scripts/codex_review.py <テーマ> video <slug>` → `13_codex_video_review.md` |
| サムネイル背景のイラスト | ChatGPT | **Codex**（画像生成。`codex exec -s workspace-write`、保存先を指定。文字を入れさせない） |
| 事実確認の裏取り | Claude | Claude（変わらず。**Codexの指摘も、原典で確かめてから反映**し、`10_review_log.md` に採否を記録） |

注意：Codexの設定の既定モデルが古いCLIで使えなかった（`gpt-6.1-sol`）→ CLIを `codex update` で更新（PowerShellで実行。Git Bashだと `tar` が失敗する）。

## 流れ（1本あたり）
1. 資料を読み、`docs/themes/<日付_slug>/08_fact_check.md`（主張ごとの根拠と原文）、`07_brief.md`、`09_script_v1.md`（番号つきの行がナレーション。〔Kn〕は根拠）を書く。
2. `codex_review.py ... script` → 指摘を原典で検証 → `09_script_v2.md`、`10_review_log.md`。
3. `data/<slug>_spec.json`（画面の定義）を、`scripts/make_spec_<slug>.py` で書く。`data/<slug>_pronunciations.json`（読み）。`data/<slug>_pronunciations.json` は `vp.py <slug> kana` で、実際の読み（kana）を確認する。
4. `vp.py <slug> story|kana|audio|bgm` → `vp.py <slug> ends`（文ごとの開始時刻）→ `vp.py <slug> still <秒>...`（レイアウト確認）。
5. `vp.py <slug> build`（6分割の並列レンダリング → 結合 → loudnorm → BGM → `qa`。黒フレーム・長さ・音量を検証）。
6. `vp.py <slug> desc|thumb`、Codexで動画の査読 → 反映 → 再ビルド → `vp.py <slug> pack`（`upload/<番号_名前>/`）。

## 画面の部品（spec の `t`）
`panel`（枠＋文章）、`stack`、`cols2`（左右2列）、`chips`、`big`、`table`、`bars`（横棒）、`line`（折れ線。年に比例）、`daybar`（1日の帯）、`swirl`（渦の概念図）、`flow`、`timeline`、`image`。出現は文番号 `at`、消えるのは `until`。章冒頭のカードは `opener`。はみ出しは `assert` で止まる。

## 学び
- 画面の文言は台本より強くなりがち（Codexの指摘の大半はこれ）。**帰属・限定（「〜とされる」「ミルンさんは」）を画面にも書く。**
- 資料の年号は、そのまま使わず、矛盾がないか確かめる（橋本論文の「1773年」は、作者の没年と合わなかった）。
- URLが違う資料を挙げられることがある（Codexが挙げたNOAAのURLは別ページだった）。**必ず開いて確認。**
- 数字は自分で検算する（江戸の一刻、コリオリの時間）。
- `pack` の前に、動画が最新か確認（古い動画をコピーしない。`vp.py pack` に検査を入れた）。
- 完成した5本：`koku`（江戸の一刻、5:48）、`gdp`（家事とGDP、6:46）、`drain`（排水の渦、4:26）、`scurvy`（壊血病とリンド、7:24）、`zenzen`（「全然」、5:53）。

## 追記（2026-10-18、第3弾の5本で増えた道具と学び）
- **道具**：`scripts/codex_thumb.py <slug> "<場面>"`（サムネ背景を Codex の画像生成で作る）／`scripts/codex_watch.py <slug> [<テーマ>]`（Codex の通し視聴。4秒おきの静止画＋字幕＋音声の測定値）／`scripts/codex_kana.py <slug> [<テーマ>]`（VOICEVOX の読みをカナにして Codex に誤読を探させる）／`scripts/finish_video.sh <slug> <テーマ>`（build→desc→thumb→pack→通し視聴→読み確認）／`scripts/make_short.py`（縦型Shorts）／`scripts/yt_api.py`（API で非公開アップロード）。
- **静止画の時刻**：ffmpeg の `fps` フィルタは時刻が約2秒ずれ、「字幕が先に出る」という偽の指摘を生んだ。**フレーム番号**で切り出す（`select='not(mod(n,N))'`）。
- **読み辞書の落とし穴**：カタカナを入れると、かえって誤読になる語がある。`水平な成分→スイヘイナセイブン` は「スイエイナ」に、`航空宇宙局→…キョク` は「キヨ'ク」になった（漢字のままのほうが正しく読めた）。辞書を足したら、必ず `vp.py <slug> kana` で読みを確認。`明治四十二年` は `明治42年` と数字に直すと「メイジヨン」を避けられた。`二分は→ニフンワ`、`原論文→ゲンロンブン`、`時刻表`、`語が→ゴガ`、`後の研究→ノチノ` のように、同音異義は前後の語ごと指定する。
- **字幕の数字変換**（`scripts/hn_text.py`）：『不十分』が『不10分』になる不具合を直した（`不十分・十分に・十分な` は変換しない）。`一・四倍` や `八十五・八度` のような中黒の小数も算用数字に直す。
- **画面の部品**：枠にタイトルを付けると高さが要る。高さ112未満は、タイトルを本文に合流させて1行にする（各 `make_spec_*.py` の `_fit`）。`assert` が出たら、まず `vp.py <slug> still <秒>...`（ `ends` の時刻）で全場面を試し描画して、直す。
- **台本の査読で多かった指摘**：条件の落ち（「距離を同じとして…」の前提が、後半の別の比較にまで掛かる）、基準の年・時点、帰属（「〜と説明している」）、「最高」の意味、年齢と年号の整合（資料自体が食い違うことがある）。結論では、数字ごとに条件を言い直す。
- **VOICEVOX**：長時間の作業中に止まることがある。`curl http://127.0.0.1:50021/version` で確認し、止まっていたら `tools/voicevox/windows-cpu/run.exe --host 127.0.0.1 --port 50021` を起動する。
- **投稿**：API の動画ファイル差し替えはできないので、直したら `yt_api.py upload <パック> --new-version`、旧版は `delete-superseded`。公開予約は Studio（時刻の入力は、入力後に画面で確認する。入らず 0:00 になったことがあった）。
