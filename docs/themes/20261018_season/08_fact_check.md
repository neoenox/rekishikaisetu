# 事実確認：季節の原因（原文を開いて確認。確認日 2026-10-17）

| 番号 | 主張 | 根拠（原文の該当） | 状態 |
|---|---|---|---|
| S1 | 季節は、地球の傾いた地軸によって生じる。年間を通して、地球の各部分が、太陽の最も直接的な光を受ける。北極が太陽の方へ傾くと北半球は夏、南極が太陽の方へ傾くと北半球は冬。両極は反対側にあるため、季節の時期も反対 | NASA Space Place「What Causes the Seasons?」https://spaceplace.nasa.gov/seasons/en/ | 確認済 |
| S2 | 地軸は、公転中も、常に同じ方向を指す。北極が太陽側に傾くのは約6月、南極が太陽側に傾くのは約12月 | 同上 | 確認済 |
| S3 | 地軸は、公転面の垂線から23.4度傾いている（NASA Science「Earth Facts」の英文は『公転面に対して』と書くが、傾きの角度の定義は垂線との角度。NASAの教材では垂線との角度と明記）。この傾きが、1年の季節の周期をつくっている | NASA Science「Earth Facts」https://science.nasa.gov/earth/facts/（"Earth's axis of rotation is tilted 23.4 degrees with respect to the plane of Earth's orbit around the Sun." "This tilt causes our yearly cycle of seasons."） | 確認済 |
| S4 | 「夏は地球が太陽に近いから暑い」は誤り。公転軌道は完全な円ではない。北半球では、地球が太陽に最も近いときに冬、最も遠いときに夏。近日点＝約9,140万マイル、遠日点＝約9,450万マイル。差は300万マイル以上だが、全体の距離に比べて大きくない。遠日点は7月、近日点は1月。「地球と太陽の距離が季節の原因ではないことの証明」 | NASA Space Place（上記） | 確認済 |
| S6 | 夏は、昼が長く、太陽の光がより急な角度で届く。地軸の傾き 23.5度は、黄道（公転面）の垂線との角度。低い緯度で…夏の昼は長く、冬の昼は短い。地球は夏に太陽から最も遠い | NASA（Goddard）教材「Stargaze」Lseason https://cdaweb.gsfc.nasa.gov/pub/documents/archived_websites/pwg.gsfc.nasa.gov/stargaze/Lseason.htm（"the 23.5 degree angle between it and the perpendicular to the ecliptic" "days are longer, and the Sun's rays arrive more steeply" "Earth is most distant from the Sun in summer!"） | 確認済 |
| S5 | 平均距離は約1億5,000万km | NASA Science「Earth Facts」 | 確認済 |

## 計算（自作）
- 距離の比：94.5÷91.4＝1.034（約3.4%遠い）。マイル→km：91.4×1.609＝約1億4,710万km、94.5×1.609＝約1億5,210万km。
- 太陽から受ける光の強さは、距離の2乗に反比例する（物理の基本）。(94.5÷91.4)²＝1.069 → 近日点は遠日点より約7%強い。
- 傾きの効果（大気を無視、北緯35度、正午）：太陽の南中高度＝90°−|緯度−太陽赤緯|。夏至（赤緯＋23.4°）＝90−11.6＝78.4°、冬至（赤緯−23.4°）＝90−58.4＝31.6°。水平な地面1m²あたりの光の強さ∝sin(高度)：sin78.4°＝0.980、sin31.6°＝0.524。比＝1.87（約1.9倍）。
- 結論の数字：距離による差は約7%、傾きによる、正午の日射の差は約1.9倍（北緯35度、大気を無視した、自作の計算）。

## 動画で言わないこと
- 「距離の影響はゼロ」（資料は「大きくない」）。
- 各地の気温の決まり方（海陸・大気・時間差など）：この動画では扱わない。
- 近日点・遠日点の具体的な日付（資料は「1月」「7月」）。

## Codex 査読後の追記
- 傾きの1.9倍は、距離を同じとし、北緯35度・夏至と冬至の南中時・水平面の単位面積あたりの日射（大気を無視）の比較。昼の長さの違いは含まない。気温の比ではない。
- 7%は、距離による日射の差（距離の差そのものは約3.4%）。
