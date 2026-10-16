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
