"""spec に、章ごとの背景イラスト（art＋shade）を差し込む。呼び出し: inject(spec, {章key: 画像名}, alpha=0.66)"""
NOTE = 'イメージ（生成画像）。実際の場面の再現ではありません'
CREDIT = '・場面のイラスト:Codex(OpenAI)による生成イラスト(イメージです。実際の場面・人物・資料の再現ではありません)'

def inject(spec, mapping, alpha=0.66):
    slug = spec['slug']
    spec['images'] = {**spec.get('images', {}), **{n: dict(file=f'assets/{slug}/art_{n}.png') for n in set(mapping.values())}}
    box = [60, 170, 1860, 850]
    for i, ch in enumerate(spec['chapters']):
        n = mapping.get(ch['key'])
        if not n:
            continue
        ch['scene'][:0] = [dict(t='art', name=n, box=box, at=0, dim=0.8, dir=1 if i % 2 == 0 else -1, note=NOTE),
                           dict(t='shade', box=box, at=0, alpha=alpha)]
    cl = spec['desc'].setdefault('credit_lines', [])
    if not any('場面のイラスト' in c for c in cl):
        for k, c in enumerate(cl):
            if c.startswith('・サムネイルの背景:Codex'):
                cl[k] = '・サムネイルの背景と場面のイラスト:Codex(OpenAI)による生成イラスト(イメージです。実際の場面・人物・資料の再現ではありません)'
                break
        else:
            cl.append(CREDIT)
