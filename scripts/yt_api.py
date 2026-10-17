"""YouTube Data API で、upload/<pack>/ を「非公開」でアップロードする。

使い方:
  python scripts/yt_api.py auth                 # 初回のみ。ブラウザで寄り道ラボのアカウントを承認
  python scripts/yt_api.py whoami               # 認証中のチャンネルを表示
  python scripts/yt_api.py upload 03_ninja_myths [--dry] [--new-version]   # 動画・サムネ・字幕を非公開で登録（作り直したときは --new-version。旧IDは superseded に残す）
  python scripts/yt_api.py delete-superseded    # 作り直しで不要になった旧版（非公開のものだけ）を削除
  python scripts/yt_api.py list                 # チャンネルの動画と公開状態

方針: このスクリプトは公開しない（privacyStatus は常に private）。公開は人が Studio で行う。
認証情報は secrets/（git管理外）。アップロード済みは data/youtube_ids.json に記録し、二重投稿を防ぐ。
"""
import json, sys
from pathlib import Path

R = Path(__file__).resolve().parents[1]
SEC = R / 'secrets'
CLIENT = SEC / 'client_secret.json'
TOKEN = SEC / 'token.json'
IDS = R / 'data' / 'youtube_ids.json'
CHANNEL_ID = 'UCN_do9fcssctmkrNsRWOO9A'  # 寄り道ラボ
SCOPES = ['https://www.googleapis.com/auth/youtube.upload',
          'https://www.googleapis.com/auth/youtube.force-ssl']
CATEGORY = '27'  # Education


def creds():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    c = Credentials.from_authorized_user_file(str(TOKEN), SCOPES) if TOKEN.exists() else None
    if c and c.expired and c.refresh_token:
        c.refresh(Request())
        TOKEN.write_text(c.to_json(), encoding='utf8')
    if not c or not c.valid:
        sys.exit('未認証です。先に: python scripts/yt_api.py auth')
    return c


def service():
    from googleapiclient.discovery import build
    return build('youtube', 'v3', credentials=creds())


def cmd_auth():
    from google_auth_oauthlib.flow import InstalledAppFlow
    if not CLIENT.exists():
        sys.exit(f'{CLIENT} がありません（Google Cloud で作成した OAuth クライアントJSONを置く）')
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT), SCOPES)
    c = flow.run_local_server(port=0, prompt='consent',
                              authorization_prompt_message='ブラウザで寄り道ラボのアカウントを選んで承認してください')
    TOKEN.write_text(c.to_json(), encoding='utf8')
    cmd_whoami()


def mine(yt):
    return yt.channels().list(part='id,snippet', mine=True).execute().get('items', [])


def cmd_whoami():
    items = mine(service())
    for it in items:
        print(it['id'], it['snippet']['title'])
    if not any(it['id'] == CHANNEL_ID for it in items):
        print('!! 寄り道ラボ(%s)ではありません。個人チャンネルへは上げません。auth をやり直してください' % CHANNEL_ID)


def load_ids():
    return json.loads(IDS.read_text(encoding='utf8')) if IDS.exists() else {}


def cmd_upload(pack, dry=False, new_version=False):
    from googleapiclient.http import MediaFileUpload
    d = R / 'upload' / pack
    title = (d / 'title.txt').read_text(encoding='utf8').strip()
    desc = (d / 'description.txt').read_text(encoding='utf8').strip()
    tags = [t.strip() for t in (d / 'tags.txt').read_text(encoding='utf8').split(',') if t.strip()]
    assert len(title) <= 100, f'タイトルが{len(title)}字'
    assert len(desc.encode('utf8')) <= 5000, f'概要欄が{len(desc.encode("utf8"))}バイト'
    assert sum(len(t) for t in tags) <= 480, 'タグが長すぎる'
    assert '<' not in title + desc and '>' not in title + desc, '概要欄/タイトルに < > は使えない'
    ids = load_ids()
    if pack in ids and not new_version:
        sys.exit(f'{pack} は登録済み: {ids[pack]["video_id"]}（二重投稿を防ぐため中止。作り直した動画を別IDで上げるなら --new-version）')
    print(f'{pack}: 「{title}」 tags={len(tags)} desc={len(desc.encode("utf8"))}B')
    if dry:
        return
    yt = service()
    if not any(it['id'] == CHANNEL_ID for it in mine(yt)):
        sys.exit('認証中のチャンネルが寄り道ラボではありません。中止')
    body = dict(snippet=dict(title=title, description=desc, tags=tags, categoryId=CATEGORY,
                             defaultLanguage='ja', defaultAudioLanguage='ja'),
                status=dict(privacyStatus='private', selfDeclaredMadeForKids=False,
                            containsSyntheticMedia=False, embeddable=True, license='youtube'))
    req = yt.videos().insert(part='snippet,status', body=body,
                             media_body=MediaFileUpload(str(d / 'video.mp4'), chunksize=8 * 1024 * 1024, resumable=True))
    resp = None
    while resp is None:
        st, resp = req.next_chunk()
        if st:
            print(f'  upload {int(st.progress() * 100)}%', flush=True)
    vid = resp['id']
    print('video id', vid, resp['status']['privacyStatus'])
    ids[pack] = dict(video_id=vid, privacy=resp['status']['privacyStatus'], via='api',
                     superseded=ids.get(pack, {}).get('superseded', []) + ([ids[pack]['video_id']] if pack in ids else []))
    IDS.parent.mkdir(exist_ok=True)
    IDS.write_text(json.dumps(ids, ensure_ascii=False, indent=1), encoding='utf8')
    yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(d / 'thumbnail.jpg'))).execute()
    print('thumbnail ok')
    yt.captions().insert(part='snippet', body=dict(snippet=dict(videoId=vid, language='ja', name='', isDraft=False)),
                         media_body=MediaFileUpload(str(d / 'subtitles_ja.srt'), mimetype='application/octet-stream')).execute()
    print('captions ok')


def cmd_delete_superseded():
    """data/youtube_ids.json の superseded に載っていて、かつ非公開の動画だけを削除する（公開済みは触らない）。"""
    yt = service()
    ids = load_ids()
    for pack, rec in ids.items():
        for vid in list(rec.get('superseded', [])):
            v = yt.videos().list(part='status,snippet', id=vid).execute()['items']
            if v and v[0]['status']['privacyStatus'] != 'private':
                print('skip (not private):', vid)
                continue
            if v:
                yt.videos().delete(id=vid).execute()
                print('deleted', vid, v[0]['snippet']['title'][:24])
            rec['superseded'].remove(vid)
            rec.setdefault('deleted', []).append(vid)
    IDS.write_text(json.dumps(ids, ensure_ascii=False, indent=1), encoding='utf8')


def cmd_list():
    yt = service()
    up = yt.channels().list(part='contentDetails', mine=True).execute()['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    ids = [i['contentDetails']['videoId'] for i in yt.playlistItems().list(part='contentDetails', playlistId=up, maxResults=50).execute()['items']]
    for v in yt.videos().list(part='snippet,status', id=','.join(ids)).execute()['items']:
        print(v['id'], v['status']['privacyStatus'], v['snippet']['title'])


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    {'auth': cmd_auth, 'whoami': cmd_whoami, 'list': cmd_list, 'delete-superseded': cmd_delete_superseded}.get(a[0], lambda: cmd_upload(a[1], '--dry' in a, '--new-version' in a) if a[0] == 'upload' else sys.exit(__doc__))()
