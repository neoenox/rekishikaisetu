from pathlib import Path
import json, numpy as np
from scipy.interpolate import RegularGridInterpolator
ROOT=Path(__file__).resolve().parents[1]
def main():
    z=np.load(ROOT/'data'/'terrain.npz');h=z['h'];xs=z['xs'];ys=z['ys'];interp=RegularGridInterpolator((ys,xs),h)
    units=json.loads((ROOT/'data'/'units.json').read_text(encoding='utf8'));a=next(u for u in units if u['id']=='kobaya');b=next(u for u in units if u['id']=='otani');t=np.linspace(0,1,300)
    x=a['x_m']*(1-t)+b['x_m']*t;y=a['y_m']*(1-t)+b['y_m']*t;elev=interp(np.column_stack([y,x]));dx=np.sqrt(np.diff(x)**2+np.diff(y)**2);dh=np.diff(elev);horizontal=float(dx.sum())
    result={'type':'inferred','source_ids':['GSI_DEM','METHOD'],'route':'straight endpoint line, not historical path','horizontal_distance_m':horizontal,'surface_distance_m':float(np.hypot(dx,dh).sum()),'ascent_m':float(np.maximum(0,dh).sum()),'descent_m':float(np.maximum(0,-dh).sum()),'max_abs_slope_deg':float(np.degrees(np.arctan(np.max(np.abs(dh)/dx)))),'sensitivity':[{'assumed_speed_m_s':v,'minutes':horizontal/v/60} for v in [.5,1,1.5]],'model_duration_seconds':3600,'model_speed_m_s':horizontal/3600,'screen_time_compression':144,'profile':{'distance_m':np.concatenate([[0],np.cumsum(dx)]).tolist(),'elevation_m':elev.tolist()},'units':[{'id':u['id'],'elevation_m':float(interp([[u['y_m'],u['x_m']]])[0])} for u in units],'excluded':['terrain changes since 1600','historic roads','mud','enemy contact','morale','canopy','weather'],'visibility':'not computed; cannot infer historic line of sight from bare modern DEM'}
    (ROOT/'out'/'analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k!='profile'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
