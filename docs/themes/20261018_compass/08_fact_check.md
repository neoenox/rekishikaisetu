# 事実確認：方位磁針と磁極（原文を開いて確認。確認日 2026-10-17）

| 番号 | 主張 | 根拠（原文の該当） | 状態 |
|---|---|---|---|
| N1 | 方位磁針は、その場所の磁場の水平成分の向きを指す。真北を得るには偏角が必要 | NOAA/NCEI「Magnetic Declination」https://www.ngdc.noaa.gov/geomag/declination.shtml（"The compass points in the directions of the horizontal component of the magnetic field" "As the compass points with local magnetic fields, declination value is needed to obtain true north."） | 確認済 |
| N2 | 偏角（磁気変化）は、磁北と真北のなす角。時間と場所で変わる。真北より東は正、西は負 | 同上（"Magnetic declination ... is the angle between magnetic north and true north." "changes over time and with location." "positive east of true north and negative when west."） | 確認済 |
| N3 | 磁極（dip pole）＝地表で地磁気が垂直になる位置。北の磁極は1831年にJames Clark Rossが北カナダで測定。カナダ天然資源省は1948〜1994年に定期測量。直近の測量では北北西へ年約55km。WMM2025の2025.0時点：北磁極 北緯85.762°・東経139.298°。地磁気極（双極子軸）は北緯80.85°・西経72.76°。磁極の定義は複数で、計算方法による | NOAA/NCEI「Wandering Geomagnetic Poles」https://www.ncei.noaa.gov/products/wandering-geomagnetic-poles | 確認済 |
| N4 | 磁北極は地理的に固定された位置ではない。日ごと・年ごとにかなりの量（約40km）動く。方位磁針の方位は、真の方位に直す必要がある | NOAA/PMEL Arctic Zone FAQ（Question 13）https://www.pmel.noaa.gov/arctic-zone/faq.html（"which is not fixed at a specific geographic location" "on the order of 40 kilometers or 25 miles" "must be converted to true directions"） | 確認済 |
| G1 | 方位磁石が指す北＝磁北。磁北が真北より東＝東偏、西＝西偏。現在の日本は南鳥島（偏角0度）を除く全域で西偏。磁気図2020.0年値で、札幌は磁北が地図の北より約10度西、那覇は約6度。全国平均では1970〜2020年の50年間で、西向きの偏角が約1.4度大きくなった。地球の極と地磁気の極は一致しない。偏角を知らないと、登山などで地図の向きが合わず道に迷うおそれ | 国土地理院「地磁気とは」https://www.gsi.go.jp/buturisokuchi/menu01_index.html | 確認済 |

## 計算（自作）
- 北極点は北緯90°。北磁極（2025.0、WMM2025）は北緯85.762°。緯度の差＝90−85.762＝4.238°。1度≒111km として、約470km（4.238×111.2≒471）。経度は関係なく、極までの角距離は余緯度（90−緯度）に等しい。

## 動画で言わないこと
- 「磁針は磁極の方向を指す」（資料は、その場所の磁場の水平成分の向き、と述べる）。
- 古い移動速度を現在値として使う（年55kmは「直近の測量」。具体的な年は、NCEIのページに書かれていない）。
- 磁極の移動と、災害・生物・気候との関係。
