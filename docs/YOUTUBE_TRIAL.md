# YouTube向け編集のお試し版

2026-10-13作成。既存の3分44秒版を残し、別ファイルで約1分39秒の実動画を出力した。

- 動画：`out/sekigahara_youtube_trial.mp4`
- 概要欄：`out/trial_video_description.txt`
- 字幕：`out/trial_subtitles.srt`
- 検証：`out/trial_quality_report.json`
- 報告：`out/TRIAL_REPORT.md`

改善した点は、冒頭からの進軍の先取り、小早川・大谷の2隊への絞り込み、全景・斜め視点・寄りの切り替え、最大28文字の短い字幕、説明と部隊位置の連続性、音量調整。軍勢が接近して重なり続けないよう、説明用の進軍を経路途中で止めている。攻撃そのものを歴史的な戦闘再現として描いたものではない。

冒頭の先取りから初期配置に切り替える場面には「陣跡の配置を確認」と表示。その後の進軍状態は、数値説明・結論でも保持する。

上下の帯を復活させず、Google・画像提供元の必要な表記だけを小さく残す。VOICEVOX等のクレジットは概要欄へ保存。

実MP4を全デコードし、2,978フレームを確認。実測音量は−18.3 LUFS、トゥルーピーク−1.5 dBFS。6場面の動画画像を取り出して合成元と照合し、枠・字幕・出典・余白を検査した。視聴維持率や発音の自然さを検証した結果ではない。

再生成は、既存の環境・取得済み素材・ローカルVOICEVOXの起動を前提として次の順序で行う。

```powershell
cd E:\rekishikaisetu
.venv\Scripts\python.exe scripts/audio.py trial 0
.venv\Scripts\python.exe scripts/build_youtube_trial.py
.venv\Scripts\python.exe scripts/verify_youtube_trial.py
```

台本は `data/trial_scenes.json`。`audio.py` の末尾の0は最小尺の指定で、このお試し版には3分までの無音を追加しない。従来版の既定の最小尺は180秒のまま。

字幕は音声の文区間を文字量で分配する近似。独立ASR・音素単位の字幕同期は未実施。地形と陣跡座標は実データだが、経路・軍勢の大きさ・服装は説明用で、当時の経路や兵数を確定するものではない。
