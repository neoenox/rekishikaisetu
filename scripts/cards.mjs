import {bundle} from '@remotion/bundler';
import {renderStill,selectComposition} from '@remotion/renderer';
import fs from 'node:fs';
import path from 'node:path';
const serveUrl=await bundle({entryPoint:path.resolve('video/index.tsx')});
const scenes=JSON.parse(fs.readFileSync('data/scenes.json','utf8'));
fs.mkdirSync('cache/cards',{recursive:true});
for(const s of scenes){
 const inputProps={title:s.title,category:s.category,source:s.source_ids.join(' / ')};
 const composition=await selectComposition({serveUrl,id:'ChapterCard',inputProps});
 await renderStill({serveUrl,composition,inputProps,output:`cache/cards/scene_${String(s.id).padStart(2,'0')}.png`,imageFormat:'png',omitBackground:true});
}
for(let level=1;level<=3;level++){
 const inputProps={title:['','LEVEL 1 / 地形と戦術マーカー','LEVEL 2 / 隊列・森林・地表材質','LEVEL 3 / 光・霧・奥行き'][level],category:'同一カメラ・同一進軍 / 移動経路は模式・時間圧縮 ×144',source:'GSI_DEM / ISHIDA / KOBAYA / LOC',level:String(level)};
 const composition=await selectComposition({serveUrl,id:'ChapterCard',inputProps});
 await renderStill({serveUrl,composition,inputProps,output:`cache/cards/level_${level}.png`,imageFormat:'png',omitBackground:true});
}
fs.writeFileSync('cache/cards/remotion.json',JSON.stringify({serveUrl,version:'4.0.377',cards:15}));
console.log('15 real Remotion cards rendered');
