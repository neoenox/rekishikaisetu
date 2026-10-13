import {chromium} from 'playwright';import fs from 'node:fs';
fs.mkdirSync('assets/earth',{recursive:true});
const browser=await chromium.launch({executablePath:'E:/rekishikaisetu/node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe',headless:true,args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1920,height:1080},locale:'en-US'});
await page.goto('https://earth.google.com/web/@35.359,136.466,200a,9500d,35y,0h,0t,0r?hl=en',{waitUntil:'domcontentloaded',timeout:90000});await page.waitForTimeout(25000);
await page.getByRole('button',{name:'Enable accessibility',exact:true}).dispatchEvent('click');await page.waitForTimeout(2000);
if(await page.getByRole('button',{name:'Dismiss',exact:true}).count())await page.getByRole('button',{name:'Dismiss',exact:true}).click();await page.waitForTimeout(1000);
await page.getByRole('button',{name:'Basemap settings, Change basemap',exact:true}).click();await page.waitForTimeout(1500);
await page.mouse.click(288,396);await page.waitForTimeout(1500);await page.mouse.click(296,132);await page.waitForTimeout(3000);
await page.mouse.click(180,1065);await page.waitForTimeout(1500);await page.screenshot({path:'assets/earth/attribution.png'});fs.writeFileSync('assets/earth/attribution_state.txt',await page.locator('body').ariaSnapshot());
await page.keyboard.press('Escape');await page.waitForTimeout(1000);await page.screenshot({path:'assets/earth/overview.png'});
const samples=[];
for(const [x,y] of [[500,300],[960,300],[1400,300],[500,540],[960,540],[1400,540],[500,800],[960,800],[1400,800]]){await page.mouse.move(x,y);await page.waitForTimeout(500);const state=await page.locator('body').ariaSnapshot();samples.push({x,y,state:state.slice(-1500)});await page.screenshot({path:`assets/earth/cal_${x}_${y}.png`});}
fs.writeFileSync('assets/earth/calibration_samples.json',JSON.stringify(samples,null,2));fs.writeFileSync('assets/earth/capture.json',JSON.stringify({url:page.url(),captured_at:new Date().toISOString(),width:1920,height:1080,method:'Google Earth web UI screenshot; no imagery tile extraction or 3D model reconstruction'},null,2));
console.log('CAPTURE COMPLETE',page.url());await browser.close();
