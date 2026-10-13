from pathlib import Path
import json,numpy as np
from PIL import ImageFont
ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((ROOT/name).read_text(encoding='utf8'))
def test_source_ids_and_conservative_categories():
    ids={s['id'] for s in load('data/sources.json')}
    for record in load('data/units.json')+load('data/events.json')+load('data/scenes.json'):
        assert record['source_ids'] and set(record['source_ids'])<=ids
    assert all(u['troop_count_range'] is None and u['position_type']=='inferred' for u in load('data/units.json'))
    assert all(e['time_historical'] is None and e['type']=='illustrative' for e in load('data/events.json'))
def test_coordinates_are_inside_terrain_and_axis_roundtrip():
    from pyproj import Transformer,CRS
    crs=CRS.from_proj4('+proj=aeqd +lat_0=35.355 +lon_0=136.472 +datum=WGS84 +units=m');reverse=Transformer.from_crs(crs,4326,always_xy=True)
    data=np.load(ROOT/'data/terrain.npz')
    for u in load('data/units.json'):
        assert data['xs'].min()<u['x_m']<data['xs'].max() and data['ys'].min()<u['y_m']<data['ys'].max()
        lon,lat=reverse.transform(u['x_m'],u['y_m']);assert abs(lon-u['lon'])<1e-7 and abs(lat-u['lat'])<1e-7
def test_all_narration_sentences_have_valid_audio_intervals():
    r=load('out/audio_report.json');assert r['all_lines_voiced'];assert 180<=r['total_seconds']<=300
    for s in r['segments']:
        assert (ROOT/s['path']).exists() and 0<=s['start']<s['end']<=r['total_seconds'] and s['rms']>.003 and s['peak']<.999
    assert all(a['end']<=b['start']+.002 for a,b in zip(r['segments'],r['segments'][1:]))
def test_overlay_text_fits_native_output():
    regular=ImageFont.truetype('C:/Windows/Fonts/YuGothM.ttc',21);bold=ImageFont.truetype('C:/Windows/Fonts/YuGothB.ttc',38)
    for s in load('data/scenes.json'):
        assert regular.getlength(s['category'])<1824 and bold.getlength(s['title'])<1824
def test_sensitivity_is_distance_over_assumed_speed_not_probability():
    a=load('out/analysis.json');assert 'win_probability' not in a
    for x in a['sensitivity']:assert abs(x['minutes']*60*x['assumed_speed_m_s']-a['horizontal_distance_m'])<1e-6
    assert a['model_speed_m_s']<1.5 and a['max_abs_slope_deg']<90
