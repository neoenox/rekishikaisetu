# 関ヶ原：実DEMを使う3D戦略解析動画PoC

Windows / RTX 4060上でローカル実行する試作システム。実データ・Blender描画・VOICEVOX音声・Remotion表示素材・FFmpeg合成を使用します。外部公開、有料契約、人間による動画編集を必要としません。

## 成果物

| ファイル | 内容 |
|---|---|
| `out/level1_terrain_markers.mp4` | 同一条件比較25秒：現代DEM、旗、地形連動の模式矢印 |
| `out/level2_terrain_troops.mp4` | 同一条件比較25秒：隊列・森林・地表材質を追加 |
| `out/level3_cinematic.mp4` | 同一条件比較25秒：照明・霧を追加 |
| `out/pilot_3to5min.mp4` | 3分59秒、12場面、日本語解説・字幕・出典・解析図表・クレジット |
| `out/comparison.png` | 同じ時刻の3品質と実測処理コスト |
| `out/subtitles.srt` | 全ナレーション対応、日本語字幕 |
| `out/quality_report.json` | 技術・地理・音声・字幕・レイアウト検証と残余リスク |
| `out/REPORT.md` | 動画リンク・処理コスト・検証結果をまとめた日本語報告 |
| `out/performance_report.json` | 品質別実測秒数、観測RAM/VRAM、採用理由 |
| `out/sources.md`, `out/assets.json` | 出典・参照箇所・権利・加工・クレジット |
| `out/assumptions.json`, `out/analysis.json` | 仮定と地形解析結果 |
| `out/audio_report.json`, `out/browser_report.json` | 全文ごとの音声区間とブラウザ回帰検証 |

最終判定は `out/quality_report.json` の実生成結果を参照してください。動画仕様はネイティブ1920×1080、実描画30fps、H.264/AACです。補間による30fps化や静止画の引き延ばしは行いません。比較は各750枚を描画し、本編は音声実長239秒に対して7170枚を描画します。本編の中間画像のみJPEG品質95を使い、ディスクI/Oを減らします。比較はPNGです。

## 最短の再実行

既存環境で全工程を再実行：

```powershell
cd E:\rekishikaisetu
pwsh -File scripts/run.ps1
```

既存のBlender描画フレームを使って字幕・合成・検証だけ再実行：

```powershell
pwsh -File scripts/run.ps1 -SkipRender
```

新しい環境の導入：Pythonを管理する `uv`、Node.js 22 LTS以上、FFmpeg/ffprobe（NVENC有効）、7-Zip、Windows游ゴシックが必要です。このPCでは確認済みです。

```powershell
pwsh -File scripts/setup.ps1
pwsh -File scripts/run.ps1
```

setupは公式Blender 4.5.3 LTS portable ZIP約400MBとVOICEVOX ENGINE 0.25.2 CPU版約1.8GBを `tools/` に取得し、作業フォルダー内に展開します。8本までのRange取得で再試行・分割キャッシュを使用します。通常の地形取得は16タイルのみです。Remotionは初回にChrome Headless Shellを取得します。バイナリ・依存パッケージ・中間描画はGit対象外です。新しいPCでは環境に合わせて7-Zipのパスを調整してください。

## 工程を個別実行

```powershell
.venv\Scripts\python.exe scripts/doctor.py
.venv\Scripts\python.exe scripts/terrain.py
.venv\Scripts\python.exe scripts/prepare_story.py
.venv\Scripts\python.exe scripts/analyze.py
# VOICEVOXを127.0.0.1:50021で起動（run.ps1が自動処理）
.venv\Scripts\python.exe scripts/audio.py
npm run cards
npm run test:layout
tools\blender-4.5.3-windows-x64\blender.exe -b -t 8 --python scripts/render_blender.py -- 1 comparison
.venv\Scripts\python.exe scripts/compose.py comparison 1
# 同じコマンドの1を2、3にして比較動画を生成
.venv\Scripts\python.exe scripts/render_pilot_parallel.py
.venv\Scripts\python.exe scripts/compose.py pilot 2
.venv\Scripts\python.exe scripts/export_sources.py
.venv\Scripts\python.exe -m pytest scripts -q
.venv\Scripts\python.exe scripts/verify.py
.venv\Scripts\python.exe scripts/write_report.py
```

任意の性能監視は `.venv\Scripts\python.exe scripts/doctor.py --monitor`。`out/monitor.stop` が存在すると終了します。ログは `logs/resources.jsonl`。再測定時はその停止ファイルを除いて起動してください。5秒ごとの観測であり、瞬間ピークを保証するものではありません。

## 地形と座標

国土地理院 `dem_png` z14を使用。RGBを24bit符号付き値へ復号し、1単位0.01m、(128,0,0)をNO DATAとして検出。NO DATAがあれば停止し、黙って穴埋めしません。関ヶ原を中心とする方位正距図法で局所メートル座標へ変換し、25m格子へ双一次再標本化。北方向は+Y、東方向は+X、標高は+Z。縦横の誇張なし。

範囲は約6.2×6.9km。現代DEMであり、1600年の河川・道路・建物・植生を復元したものではありません。DEMには実地形の情報がありますが、25m格子にしたことで微細地形は失われます。出典表示は「地理院タイル（標高）を加工」。URL・取得日・ハッシュ・再標本化方式は `data/terrain_manifest.json` に記録します。

## 歴史の扱い

岐阜関ケ原古戦場記念館の石田三成・小早川秀秋・徳川家康コース、および関ケ原町歴史民俗学習館の陣跡説明を参照しています。これらは公式の史跡解説であり、一次史料を直接校訂した証明とは区別します。

陣跡座標は株式会社CCL 大垣支社「関ヶ原位置情報リスト2013年度」（CC BY 3.0）の地点を局所座標化。現存する記念地点と、1600年に軍勢が占めた陣域は同一ではありません。150mの円は本PoCの仮定であり、測定された誤差保証ではありません。表示対象は石田三成、小早川秀秋、大谷吉継、徳川家康の4地点です。曖昧な全軍配置や兵数・分単位時刻は作りません。

動く小早川隊と大谷隊の関係は公式解説に帰属させ、道筋は仮説として表示します。二点間の直線を使った接地動作試験で、実際の進軍経路ではありません。旗・兵士は拡大した無地の象徴モデル、各隊30体は実兵数ではありません。森林はプロシージャル演出、霧も歴史上の気象再現ではありません。

威嚇射撃は出典でも「一説」であり、確定した射撃として再現しません。月日の暦の混同を避け、本編の年表現は慶長五年（1600年）に限定します。出典・主張分類は `data/sources.json`、`units.json`、`events.json`、`scenes.json` で管理します。

## 解析モデル

測るのは仮説経路の水平距離・地表距離・累積上り下り・勾配と、速度の仮定を変えた単純な所要時間です。水平距離約1.45kmを0.5 / 1.0 / 1.5m/sで割る感度分析を出力します。道路、ぬかるみ、敵との接触、士気、指揮、当時の植生は計算しません。勝率・戦闘結果は出しません。歴史的な見通しは植生・気象が不明のため解析不能と明示します。

比較の模型時間は3600秒、表示は25秒に圧縮。画面で「史実時刻ではない」と表示します。本編は第6場面のみ隊列を進め、それ以外は配置や地形の説明に合わせた位置を保持。場面ごとに全体・笹尾山・松尾山・本陣側へ視点を切り替えます。

## 検証と限界

- 4動画の存在、全フレームデコード、H.264/AAC、FHD/30fps、尺、音声トラックを検証。
- 比較の冒頭・中間・終盤、本編各章の冒頭・中間・末尾から抽出し、黒画面・画素分散を検査。
- 全文のPCM音声長・RMS・ピーク、字幕時刻・非重複、固有名詞辞書を検証。
- 全描画フレームで兵士底面中心と三角形DEMの接触誤差を検証。拡大モデルの底面端や装備の斜面貫通は未保証。
- ラベルは全合成フレームで矩形の衝突を避け、毎秒レイアウトを記録・検査。画面外・衝突するラベルは省略数を記録。
- カメラの連続性を検査し、章境界の意図したカットを記録。
- 出典IDの参照整合性・権利とクレジットを検査。歴史的意味を完全自動で証明するものではない。
- PlaywrightはRemotion生成画像のデコード・サイズ・表示領域を検証。独立OCRと独立日本語ASRによる全文検証は未実施。

有料契約・外部公開・GitHub操作は行っていません。人物の肖像や既存の軍旗画像を使用していません。ライセンスに関する記録は使用範囲の確認であり、将来の用途変更まで包括的に許可するものではありません。

## 編集・拡張

台本と根拠は `scripts/prepare_story.py` が生成するJSONが入口です。テーマから自由に歴史的断定を生成する汎用LLMシステムではなく、関ヶ原の出典確認済み入力を持つ再利用可能なPoCです。他の戦いへ適用する場合は、地形範囲・史料・座標・台本・仮定を更新し、同じ検証ゲートを通します。音声は文ごとにクエリのハッシュでキャッシュし、変更箇所だけ再生成します。
