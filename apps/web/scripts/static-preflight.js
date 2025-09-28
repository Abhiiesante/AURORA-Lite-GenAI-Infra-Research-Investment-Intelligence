#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const appDir = path.join(__dirname, '..', 'app');
function walk(dir, out=[]) { for (const e of fs.readdirSync(dir)) { const full = path.join(dir,e); const s=fs.statSync(full); if (s.isDirectory()) walk(full,out); else out.push(full);} return out; }
const files = walk(appDir); const pageFiles = files.filter(f=>/page\.tsx?$/.test(f));
const dynamicWarnings = [];
for (const f of pageFiles){ if (f.includes('[') && !/generateStaticParams\s*\(/.test(fs.readFileSync(f,'utf8'))) dynamicWarnings.push(path.relative(appDir,f)); }
console.log('\n[static-preflight]');
if (dynamicWarnings.length){ console.log('Dynamic segment pages missing generateStaticParams:'); dynamicWarnings.forEach(w=>console.log(' -',w)); }
else console.log('All dynamic segment pages define generateStaticParams');
console.log('Heavy client pages will hydrate only in browser (ssr:false): market-map, kg, explorer, trends, dashboard');