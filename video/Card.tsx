import React from 'react';
import {AbsoluteFill} from 'remotion';
export const ChapterCard:React.FC<{title:string; category:string; source:string; level?:string}>=({title,category,source,level})=><AbsoluteFill style={{fontFamily:'Yu Gothic, sans-serif',color:'#f5f3e8',background:'transparent'}}>
 <div data-box="header" style={{position:'absolute',left:0,top:0,width:1920,height:200,background:'linear-gradient(#081b29f5,#081b29d9)',padding:'18px 48px',boxSizing:'border-box',lineHeight:1.2}}>
  <div style={{fontSize:22,letterSpacing:3,color:'#a7b9bd'}}>SEKIGAHARA / TERRAIN & STRATEGY {level||''}</div>
  <div style={{fontSize:52,fontWeight:700,marginTop:8}}>{title}</div>
  <div style={{fontSize:30,color:'#efc976',marginTop:5}}>{category}</div>
 </div>
 <div data-box="footer" style={{position:'absolute',bottom:0,left:0,width:1920,height:65,background:'#081b29ed',boxSizing:'border-box',padding:'14px 48px',fontSize:24}}>出典：{source}　|　地理院タイル（標高）を加工　|　VOICEVOX:四国めたん</div>
 <div data-box="legend" style={{position:'absolute',right:45,top:220,width:390,padding:18,background:'#081b29f5',borderLeft:'3px solid #c5a86c',fontSize:28,lineHeight:1.55,boxSizing:'border-box'}}>現代DEM / 縮尺1:1<br/><span style={{color:'#4e9bff'}}>● 西軍</span>　<span style={{color:'#ff6255'}}>● 東軍</span><br/><span style={{color:'#efc976'}}>● 小早川 / 模式経路</span><br/>位置推定：仮定 ±150m<br/>旗・兵士：説明用拡大<br/>植生・霧：演出</div>
</AbsoluteFill>;
