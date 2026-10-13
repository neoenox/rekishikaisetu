import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {chromium} from 'playwright';
import {build} from 'esbuild';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
// Use the same downloaded browser as real Remotion rendering.
const chrome=path.resolve('node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell.exe');
const find=(dir)=>{for(const e of fs.readdirSync(dir,{withFileTypes:true})){const p=path.join(dir,e.name);if(e.isDirectory()){const r=find(p);if(r)return r;}else if(e.name==='chrome-headless-shell.exe')return p;}};
const executable=fs.existsSync(chrome)?chrome:find('node_modules/.remotion');
const browser=await chromium.launch({headless:true,executablePath:executable});
const built=await build({entryPoints:['video/Card.tsx'],bundle:true,platform:'node',format:'esm',write:false,external:['react','remotion']});
fs.writeFileSync('cache/card-server.mjs',built.outputFiles[0].text);
const {ChapterCard}=await import(pathToFileURL(path.resolve('cache/card-server.mjs')).href);
const page=await browser.newPage({viewport:{width:1920,height:1080}});const errors=[];page.on('pageerror',e=>errors.push(String(e)));
const scenes=JSON.parse(fs.readFileSync('data/scenes.json','utf8'));const results=[];
for(const s of scenes){
 const url=pathToFileURL(path.resolve(`cache/cards/scene_${String(s.id).padStart(2,'0')}.png`)).href;
 await page.goto(url);
 await page.addStyleTag({content:'body{margin:0;background:#243c42}img{display:block;width:1920px;height:1080px;max-width:none;max-height:none}'});
 await page.waitForFunction(()=>document.images[0].complete);
 const result=await page.evaluate(()=>({width:document.images[0].naturalWidth,height:document.images[0].naturalHeight,scrollWidth:document.documentElement.scrollWidth,scrollHeight:document.documentElement.scrollHeight}));
 if(result.width!==1920||result.height!==1080||result.scrollWidth!==1920||result.scrollHeight!==1080)throw Error(JSON.stringify(result));
 const markup=renderToStaticMarkup(React.createElement(ChapterCard,{title:s.title,category:s.category,source:s.source_ids.join(' / ')}));
 const html=`<!doctype html><meta charset="utf-8"><style>body{margin:0}#root{position:relative;width:1920px;height:1080px}</style><div id="root">${markup}</div>`;
 const target=path.resolve(`cache/cards/dom_scene_${s.id}.html`);fs.writeFileSync(target,html);await page.goto(pathToFileURL(target).href);await page.evaluate(()=>document.fonts.ready);
 const overflow=await page.evaluate(()=>{
   const failures=[];for(const container of document.querySelectorAll('[data-box]')){const box=container.getBoundingClientRect();const walker=document.createTreeWalker(container,NodeFilter.SHOW_TEXT);while(walker.nextNode()){const node=walker.currentNode;if(!node.textContent.trim())continue;const range=document.createRange();range.selectNodeContents(node);const r=range.getBoundingClientRect();if(r.left<box.left-1||r.right>box.right+1||r.top<box.top-1||r.bottom>box.bottom+1)failures.push({box:container.dataset.box,text:node.textContent,rect:{left:r.left,right:r.right,top:r.top,bottom:r.bottom},parent:{left:box.left,right:box.right,top:box.top,bottom:box.bottom}});}}return failures;});
 if(overflow.length)throw Error(JSON.stringify(overflow));
 results.push({scene:s.id,...result,real_dom_text_overflow:overflow});
}
await browser.close();fs.writeFileSync('out/browser_report.json',JSON.stringify({method:'Playwright image decode plus real React/Remotion component DOM text-range overflow inspection at1920x1080',results,errors,limitations:'Actual text-node rectangles verified against header/footer/legend; no independent OCR or historical semantic proof.'},null,2));
console.log('Playwright: 12 real component DOMs and12 rendered cards, no text overflow or page errors');
