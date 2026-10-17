# YouTube 非公開アップロード手順（Claudeがブラウザ操作で行う）

公開直前（**非公開の下書き**）までをClaudeが行う手順。**「公開」ボタンは押さない**（公開はユーザーが行う）。
実績：本能寺（2026-10-16）。世界地図はユーザーがファイル選択を行い、Claudeがメタデータ入力。

## 0. 前提
- チャンネル：**寄り道ラボ**（チャンネルID `UCN_do9fcssctmkrNsRWOO9A`）。個人チャンネル（もち、`UC4PnzZgTs6uC_zzhI_0gDaw`）には**何もアップしない**。
- 素材：`upload/<番号_名前>/`（`video.mp4` `thumbnail.jpg` `subtitles_ja.srt` `title.txt` `description.txt` `tags.txt`）。`scripts/make_upload_pack.py` で作る。
- ツール：Claude in Chrome（`tabs_context_mcp` → `createIfEmpty:true` → 自分用タブを使う）。
- 制約：
  - `file_upload` は**10MB未満**、かつ**セッションが読めるフォルダ**のみ（`upload/` は不可。`out/` は可）。サムネイル・字幕は `out/` のコピーを使う（`cmp` で同一確認）。
  - ブラウザのファイル選択ダイアログは操作できない → 動画本体は下の「§2 ローカルサーバー方式」で渡す。

## 1. アカウントの確認と切り替え
1. `https://studio.youtube.com` を開く。最初は**個人チャンネル（もち）**のことが多い。
2. 右上アバター → 「アカウントを切り替える」→ **寄り道ラボ**（kaenozu系アカウント）を選ぶ。
3. 左上のチャンネル名が「寄り道ラボ」であることを確認。`https://studio.youtube.com/channel/UCN_do9fcssctmkrNsRWOO9A/videos/upload` を開く。
4. 画面が真っ黒の間は8〜10秒待つ。
5. 開いている別タブ（別セッションのタブ）は「グループ外」になるので、`tabs_context_mcp(createIfEmpty:true)` で出る**自分のタブ**を使う。

## 2. 動画本体の渡し方（ローカルサーバー方式）
ユーザーの許可を、**チャットで明示的に**得てから行う（実績：許可後に実行できた。許可前はセキュリティ判定で拒否された）。
1. CORS付きの一時サーバーを `127.0.0.1:8765` で起動（対象の `upload/<動画>/` をカレントにする）。スクリプトは下記。バックグラウンド実行。
2. Studio右上「作成」→「動画をアップロード」でダイアログを開く（「ファイルを選択」は押さない）。
3. ブラウザに **「ローカルネットワークへのアクセス」許可**が出ると、`fetch` が `pending` のまま止まる（画面には映らない）。→ **ユーザーに「許可」を押してもらう**。テストは `fetch('http://127.0.0.1:8765/title.txt')` の結果を `window.__r` に入れて確認。
4. 許可後、次のJSで `input[type=file]`（Shadow DOM内もあり）に動画を渡す（結果は `window.__up` に入れる。`javascript_tool` はPromiseの戻り値を返さない）：

```js
window.__up='start';(async()=>{try{function find(root){const r=root.querySelector('input[type=file]');if(r)return r;for(const e of root.querySelectorAll('*')){if(e.shadowRoot){const x=find(e.shadowRoot);if(x)return x}}return null}
const inp=find(document);if(!inp){window.__up='no input';return}
const r=await fetch('http://127.0.0.1:8765/video.mp4');const b=await r.blob();const f=new File([b],'video.mp4',{type:'video/mp4'});
const dt=new DataTransfer();dt.items.add(f);inp.files=dt.files;inp.dispatchEvent(new Event('change',{bubbles:true}));window.__up='set '+f.size}catch(e){window.__up='err '+e}})();'ok'
```
5. 10秒ほど待って `window.__up` が `set <バイト数>` になり、ダイアログが「詳細」画面（「非公開として保存済み」）になれば成功。
6. **アップロードが終わるまでタブとダイアログを閉じない**（316MBで約30〜60分。進捗は左下「アップロード中（n%）」）。
7. 終わったらサーバーを停止（`TaskStop` またはプロセス終了）。

サーバースクリプト（`cors_server.py`）：
```python
import http.server
class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin','*');self.send_header('Access-Control-Allow-Private-Network','true');super().end_headers()
    def do_OPTIONS(self):
        self.send_response(204);self.send_header('Access-Control-Allow-Methods','GET');self.send_header('Access-Control-Allow-Headers','*');self.end_headers()
http.server.ThreadingHTTPServer(('127.0.0.1',8765),H).serve_forever()
```

## 3. 「詳細」画面の入力（アップロード中でも可）
- **タイトル**：欄を左クリック → `ctrl+a` → `type`（既定は「video」）。
- **説明**：欄を左クリック → `ctrl+a` → `Delete`（チャンネル既定の文が入っている）→ `type`。**`description.txt` の末尾に「■ このチャンネルについて／寄り道ラボは、ふと気になったことを、資料やデータで調べる解説チャンネルです。」を足す**（本能寺は足した）。外部リンクは「動画認証」完了までクリック不可の注意が出る（赤字の枠はそれ）。
- **サムネイル**：`find`「thumbnail file input」→ `file_upload`（`out/` のJPEG）。
- **視聴者**：「いいえ、子ども向けではありません」。
- **「すべて表示」**を開く：
  - AIの使用：ユーザー方針は**「いいえ」**（生成画像は様式化した錦絵風で、現実に見せるものではない／概要欄に明記）。実写に見える生成物を入れた場合は再検討。
  - タグ：カンマ区切りで `tags.txt` をそのまま `type`。
  - 動画の言語：プルダウンを開き、`find` で「日本語」の option を出して**クリック**（型入力の検索は効かない。**キー入力が別タブ（YouTube視聴ページ）を開くことがある** → 開いたら閉じる）。
  - 自動チャプター等は既定のまま。
- 画面は小さいので、ダイアログ内のスクロールは**右側（プレビュー列）の上**でマウスホイールを回す（説明欄の上だと説明欄だけが動く）。

## 4. 残りの手順
1. アップロード完了・処理後、「次へ」で「動画の要素」→「チェック」→「公開設定」。
2. 「公開設定」は**「非公開」**のまま。**公開／スケジュールは押さない**。「保存」（または閉じる）で下書き保存。
3. 字幕（実績：本能寺 2026-10-17）：`https://studio.youtube.com/video/<動画ID>/translations` を開く。**動画の言語（日本語）を先に設定**。元の言語の字幕は、一覧（「翻訳」表）には出ず、「字幕を編集」から開く。
   - 「手動でアップロード」→「タイムコードあり」→ `file_upload` は、**エラー（「字幕をアップロードできませんでした」）または無反応になることがあった**。
   - 確実な手順：「字幕を編集」（自動生成の下書きが入っていることがある。文字化けしていても、そのまま上書き）→ 右上の「⋮」→「ファイルをアップロード」→「タイムコードあり」→「続行」→ `find`「file input」→ `file_upload`（`out/<slug>_subtitles.srt`）→ 内容が読み込まれたら右上「公開」（動画の公開ではなく、字幕トラックの公開。動画は非公開のまま）。
   - 確認：「公開」の直後に、画面下に「日本語の字幕を公開しました」と出ることを確認する（**編集画面に内容が残っているだけでは、公開済みの証拠にならない**。1回目は、内容は読み込まれたが、公開されていなかった）。**元の言語（動画の言語）の字幕は、「言語」ページの一覧（翻訳の表）には出ない**。公開の確認は、トースト表示か、プレビューの再生画面（CCボタン）で行う。
4. 一覧で「非公開」「サムネイル」「長さ」を確認し、ユーザーに報告（公開前チェックリストの未了項目も添える）。

## 5. 公開前に残るユーザー作業（動画ごと）
- 通しの視聴確認、権利・原著の確認（本能寺：`docs/HONNOJI_VERIFICATION_LIST.md`、`docs/HONNOJI_RIGHTS_LEDGER.md`。忍者：`docs/themes/20261016_ninja/08_fact_check.md` の宿題と画像の権利）。
- 動画認証（概要欄の外部リンクをクリック可能にする。最大24時間）。

## 追記（2026-10-17、6本をアップロードした実績）
- **座標は画面ごとに変わる**（ビューポートが698と744の2種類）。クリックは、`find` で取れる `ref` を使うのが安全：「いいえ、子ども向けではありません」(radio)、「すべて表示」(button)、「いいえ、AI を使用していません」(radio)、「タグ」(textbox)、「動画の言語」(button)。言語は、ボタンを開く → `find`「日本語 option」→ `scroll_to` → スクリーンショットで位置を見てクリック。
- 入力は `browser_batch` にまとめられる（タイトル→説明→サムネイル用の `find`）。説明の改行は `
`、引用符は `\"`。
- 処理中の動画（「動画を処理しています」）は、字幕エディタが開かない／自動生成中の表示になる。**先に全本の詳細を入れ、後から字幕を入れる**と効率がよい。
- 字幕の「続行」ボタンの位置は、画面で2種類（(896,429)と(896,407)）。スクリーンショットで確認する。「ファイルをアップロード」の項目は、1回目のクリックが効かないことがある（再クリック）。
- 確認は、再生ページ `watch?v=<ID>` で `ytInitialPlayerResponse.captions...captionTracks` を読む（手動の「日本語」トラックが付いていればOK）。
- 動画ID：忍者 FmJrf-t7ro8／一刻 7zQoHDwkHxk／家事とGDP mk0oaydOqvE／排水 z4QFttJegKQ／壊血病 ui62BcJ0lSc／全然 MtOTnnj5pF0／本能寺 CGDD1uyr9Y8／世界地図 0gpV-8L1yvg。

## 追記（2026-10-17、APIでのアップロード）
- `scripts/yt_api.py`（YouTube Data API v3）で、動画・サムネイル・日本語字幕を**非公開で**登録できる。認証は初回のみ `python scripts/yt_api.py auth`（Google Cloud のプロジェクト `yorimichi-lab-upload`、外部・テスト中、テストユーザー kaenozu@gmail.com。`secrets/` は git 管理外。テスト中の認証は7日で失効）。
- 使い方: `python scripts/yt_api.py upload <パック名> [--dry] [--new-version]`、`list`、`whoami`。作り直した動画は `--new-version` で別IDに上げ、旧IDは `data/youtube_ids.json` の `superseded` に残す（YouTubeは動画ファイルの差し替え不可）。
- 審査前のAPIプロジェクトの動画は非公開に固定される。公開・スケジュールは Studio で行う。
- Codexの通し視聴: `python scripts/codex_watch.py <slug> [<テーマ>]`。静止画は**フレーム番号**で切り出す（fpsフィルタは時刻が約2秒ずれ、字幕のずれの偽の指摘が出た）。Codexは音を聞けない。
