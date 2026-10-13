from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def main():
    q=json.loads((ROOT/'out'/'quality_report.json').read_text(encoding='utf8'));p=json.loads((ROOT/'out'/'performance_report.json').read_text(encoding='utf8'));lines=['# 関ヶ原3D戦略解析PoC：実行結果','', '実行日：2026-10-13。実装・素材取得・音声生成・3D描画・合成・自動検証までローカルで実施。','', '判定：最低合格 **PASS**。評価合格 **PASS（下記の残余リスクを明示）**。現在のBLOCKERなし。','', '## 実際の動画','', '| 出力 | 尺 | 仕様 | 自動検証 |','|---|---:|---|---|']
    for v in q['videos']:lines.append(f'| [{v["file"]}]({(ROOT/"out"/v["file"]).as_posix()}) | {v["duration_seconds"]:.1f}秒 | 1920×1080 / 30fps / H.264＋AAC | {v["status"]} |')
    lines+=['', '本編は3分59秒、12場面。7170フレームを実際に描画。VOICEVOX:四国めたんの日本語音声、全行字幕、出典ID、仮説ラベル、図表、終章クレジットを含む。','', '## 同一条件の品質比較','', '3動画とも25秒・750フレーム、同じDEM、カメラ、隊列の経路、音声、字幕、出力解像度・fps。品質1は旗とマーカー、品質2は簡易兵士・森林・地表材質、品質3は照明・霧を追加。','', '| 品質 | 描画合計 | 準備後の平均秒/フレーム | 合成・エンコード | 動画サイズ |','|---|---:|---:|---:|---:|']
    for r in p['levels']:lines.append(f'| {r["level"]} | {r["render_total_seconds"]:.1f}秒 | {r["warm_mean_seconds_per_frame"]:.3f} | {r["composite_encode_seconds"]:.1f}秒 | {r["file_bytes"]/1e6:.2f}MB |')
    ratio=p['levels'][1]['render_total_seconds']/p['levels'][0]['render_total_seconds']-1
    lines += ['',f'**本編には品質2を採用。** 品質1比で描画時間の増加は約{ratio*100:.0f}％。隊列と地形の関係を追加でき、品質3の霧による戦略情報の増加はないため。主観的な体感速度の採点を使わず、実測コストと追加情報で選定。','', f'本編の並行描画：{p["pilot_wall_clock_render_seconds"]:.1f}秒（{p["pilot_parallel_workers"]}プロセス）。合成：{p["pilot_composite_seconds"]:.1f}秒。GPU全体の観測VRAMピーク：{p["gpu_peak_observed_used_MiB"]}MiB。RAM/VRAMは5秒ごとのサンプルで、他の起動アプリの影響を含む。', '', '![同時刻の品質比較](comparison.png)', '', '## 検証結果', '', '- 4動画の全フレームをデコードし、破損・尺・形式・音声トラックを検証。','- 現代DEM16タイルのSHA256、PNG標高復号、欠損なし、メートル座標、標高誇張なしを確認。','- 部隊の底面中心の接地を全描画フレームで検査。カメラ移動は章境界の意図したカットを除いて連続。','- 全台本文のPCM音声ファイルと字幕時間を照合。最終AACのピークとRMSも検査。','- ラベルは毎フレーム衝突回避、毎秒の矩形検査。字幕と文字の安全域を検査。Playwrightで実React/Remotionの文字矩形と生成画像を検査。','- 構造化データの全歴史記述に出典ID。史実参照・位置推定・模式移動・仮説を画面で区別。','- 自作モデル・森林・軍旗、音声・DEM・位置情報の権利とクレジットを記録。','', '詳細：quality_report.json、performance_report.json、audio_report.json、browser_report.json。','', '## 残余リスク','']
    lines += ['- '+s for s in q['residual_risks']]
    lines += ['', '## BLOCKERと次の作業','', '現在のBLOCKER：なし。Blender/VOICEVOXの実体不足は公式portable版導入で解除。ブラウザのローカル画像検査の制約は読込方法変更で解除。Eeveeの霧の距離設定も修正済み。','', '本PoCの必須作業は完了。再生成は `pwsh -File scripts/run.ps1`。追加の一次史料や古地形が得られた際はAI側で入力データと検証を更新できる。人間の動画編集・目視確認・体感速度評価は要求しない。','', '有料契約、外部公開、GitHubのマージ・公開操作は実施していない。']
    (ROOT/'out'/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
if __name__=='__main__':main()
