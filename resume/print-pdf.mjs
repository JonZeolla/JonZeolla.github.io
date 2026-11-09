import { spawn } from 'node:child_process';
import { writeFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

// Defaults: the resume next to this script, printed to the file the site serves at /resume.pdf.
const URL = process.argv[2] ?? new globalThis.URL('./Jon Zeolla Resume.html', import.meta.url).href;
const OUT = process.argv[3] ?? new globalThis.URL('../public/resume.pdf', import.meta.url).pathname;
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const PORT = 9333;
const profile = mkdtempSync(join(tmpdir(), 'cdp-'));

const chrome = spawn(CHROME, [
  '--headless=new', '--disable-gpu', `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${profile}`, '--no-first-run', '--no-default-browser-check',
  'about:blank',
], { stdio: 'ignore' });

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function getWsUrl() {
  for (let i = 0; i < 50; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PORT}/json/version`);
      const j = await r.json();
      if (j.webSocketDebuggerUrl) return j.webSocketDebuggerUrl;
    } catch {}
    await sleep(200);
  }
  throw new Error('no devtools endpoint');
}

const wsUrl = await getWsUrl();
const ws = new WebSocket(wsUrl);
let id = 0;
const pending = new Map();
const send = (method, params = {}, sessionId) => new Promise((resolve, reject) => {
  const msgId = ++id;
  pending.set(msgId, { resolve, reject });
  ws.send(JSON.stringify({ id: msgId, method, params, sessionId }));
});

await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
ws.onmessage = (ev) => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) {
    const { resolve, reject } = pending.get(m.id);
    pending.delete(m.id);
    m.error ? reject(new Error(m.error.message)) : resolve(m.result);
  }
};

// Attach to a page target
const { targetInfos } = await send('Target.getTargets');
let target = targetInfos.find(t => t.type === 'page');
const { sessionId } = await send('Target.attachToTarget', { targetId: target.targetId, flatten: true });

await send('Page.enable', {}, sessionId);
await send('Runtime.enable', {}, sessionId);
await send('Page.navigate', { url: URL }, sessionId);
await sleep(1500);

// Poll until the contribution-graph image has loaded
for (let i = 0; i < 40; i++) {
  const { result } = await send('Runtime.evaluate', {
    expression: `(() => { const i=document.querySelector('img[src*="ghchart"]'); return !!(i && i.complete && i.naturalWidth>0); })()`,
    returnByValue: true,
  }, sessionId);
  if (result.value) break;
  await sleep(300);
}
await sleep(800);

const { data } = await send('Page.printToPDF', {
  printBackground: true,
  preferCSSPageSize: true,
  marginTop: 0, marginBottom: 0, marginLeft: 0, marginRight: 0,
  // NOTE: generateTaggedPDF is NOT the data-detector-box fix (that's text-level — see
  // AGENTS.md gotcha #3). The box appeared on tagged and untagged PDFs alike. Untagged here is
  // just a debugging leftover; flip to true if you want an accessible/tagged PDF.
  generateTaggedPDF: false,
  generateDocumentOutline: false,
}, sessionId);

writeFileSync(OUT, Buffer.from(data, 'base64'));
console.log('wrote', OUT);
ws.close();
chrome.kill();
process.exit(0);
