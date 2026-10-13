import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {chromium} from 'playwright';
// Use the same downloaded browser as real Remotion rendering.
const chrome=path.resolve('node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell.exe');
const find=(dir)=>{for(const e of fs.readdirSync(dir,{withFileTypes:true})){const p=path.join(dir,e.name);if(e.isDirectory()){const r=find(p);if(r)return r;}else if(e.name==='chrome-headless-shell.exe')return p;}};
const executable=fs.existsSync(chrome)?chrome:find('node_modules/.remotion');
const browser=await chromium.launch({headless:true,executablePath:executable});
const page=await browser.newPage({viewport:{width:1920,height:1080}});const errors=[];page.on('pageerror',e=>errors.push(String(e)));
const scenes=JSON.parse(fs.readFileSync('data/scenes.json','utf8'));const results=[];
for(const s of scenes){
 const url=pathToFileURL(path.resolve(`cache/cards/scene_${String(s.id).padStart(2,'0')}.png`)).href;
 await page.goto(url);
 await page.addStyleTag({content:'body{margin:0;background:#243c42}img{display:block;width:1920px;height:1080px;max-width:none;max-height:none}'});
 await page.waitForFunction(()=>document.images[0].complete);
 const result=await page.evaluate(()=>({width:document.images[0].naturalWidth,height:document.images[0].naturalHeight,scrollWidth:document.documentElement.scrollWidth,scrollHeight:document.documentElement.scrollHeight}));
 if(result.width!==1920||result.height!==1080||result.scrollWidth!==1920||result.scrollHeight!==1080)throw Error(JSON.stringify(result));
 results.push({scene:s.id,...result});
}
await browser.close();fs.writeFileSync('out/browser_report.json',JSON.stringify({method:'Playwright image decode and viewport regression; cards are real Remotion browser output',results,errors,limitations:'PNG viewport regression does not independently OCR or validate DOM text overflow; Pillow validates text metrics separately.'},null,2));
console.log('Playwright: 12 cards decoded at 1920x1080, no overflow or page errors');
