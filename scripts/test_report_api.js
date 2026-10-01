#!/usr/bin/env node
// Tests for api/report.js with a fake GitHub. No network, no token needed.
//   node scripts/test_report_api.js
const assert = require('assert');
process.env.REPORTS_TOKEN = 'test';
process.env.REPORTS_REPO = 'me/reports';
const handler = require('../api/report.js');

const HOST = 'halo-visual-bible.vercel.app';
const good = () => ({
  v: 1, slug: 'mark', chapter: 3, verse: 1, last: 6, scene: 'mark.3.1', file: 'halo_edit_00079_.png',
  audio: '/audio/mark/mark-03-01.mp3?v=85179a1f', kind: 'image', reason: 'limbs',
  note: 'Six fingers on the left hand. @someone [x](http://evil) ~~~ break', url: `https://${HOST}/mark#s3-1`, website: '', t: 9000,
});
let ipN = 0;
function call(body, { origin = `https://${HOST}`, method = 'POST', ip } = {}) {
  return new Promise((done) => {
    const res = { headers: {}, code: 0, setHeader(k, v) { this.headers[k] = v; },
      status(c) { this.code = c; return this; }, json(j) { done({ code: this.code, j }); } };
    handler({ method, body, headers: { host: HOST, origin, 'x-forwarded-for': ip || `10.0.0.${++ipN}` } }, res);
  });
}

// fake GitHub: records calls; search finds whatever is in `open`
let calls = [], open = [], failLabels = false;
global.fetch = async (url, opts = {}) => {
  const body = opts.body ? JSON.parse(opts.body) : null;
  calls.push({ url, method: opts.method || 'GET', body });
  const ok = (j) => ({ ok: true, status: 200, json: async () => j });
  if (url.includes('/search/issues')) return ok({ items: open });
  if (url.endsWith('/issues') && failLabels && body.labels) return { ok: false, status: 422, json: async () => ({}) };
  if (url.endsWith('/issues')) return ok({ number: 7 });
  if (url.endsWith('/comments')) return ok({ id: 1 });
  throw new Error('unexpected ' + url);
};

(async () => {
  let r;
  r = await call(good());
  assert.strictEqual(r.code, 200); assert.strictEqual(r.j.added, false);
  const made = calls.find((c) => c.method === 'POST');
  assert.ok(made.url.endsWith('/repos/me/reports/issues'));
  assert.strictEqual(made.body.title, 'mark.3.1 picture: extra or missing limbs, hands or fingers (Mark 3:1–6)');
  assert.deepStrictEqual(made.body.labels, ['reader-report', 'image', 'book:mark']);
  assert.ok(made.body.body.includes('| Image | `halo_edit_00079_.png` |'));
  assert.ok(made.body.body.includes(`![mark.3.1](https://${HOST}/images/full/halo_edit_00079_.webp)`));
  assert.ok(made.body.body.includes('~~~text\nSix fingers') && made.body.body.includes('~ ~ ~ break\n~~~'), 'note is fenced and cannot break out');
  console.log('ok  files a new issue');

  calls = []; open = [{ number: 3, title: made.body.title }, { number: 4, title: 'mark.3.10 picture: x' }];
  r = await call(good());
  assert.strictEqual(r.j.added, true);
  assert.ok(calls.some((c) => c.url.endsWith('/issues/3/comments')));
  assert.ok(!calls.some((c) => c.url.endsWith('/issues') && c.method === 'POST'));
  console.log('ok  a repeat becomes a comment on the open issue');

  calls = []; open = []; failLabels = true;
  r = await call(good());
  assert.strictEqual(r.code, 200);
  assert.strictEqual(calls.filter((c) => c.url.endsWith('/issues')).length, 2);
  failLabels = false;
  console.log('ok  label trouble still files the issue');

  calls = [];
  for (const [name, patch] of [['honeypot', { website: 'http://spam' }], ['too fast', { t: 300 }], ['no timer', { t: undefined }]]) {
    r = await call({ ...good(), ...patch });
    assert.strictEqual(r.code, 200); assert.strictEqual(calls.length, 0, name + ' must not reach GitHub');
  }
  console.log('ok  honeypot and too-fast reports are dropped quietly');

  for (const [name, patch] of [
    ['book', { slug: 'hezekiah' }], ['chapter', { chapter: 0 }], ['range', { last: 0 }], ['kind', { kind: 'video' }],
    ['reason', { reason: 'name' }], ['file', { file: '../x.png' }], ['audio', { audio: 'https://evil/x.mp3' }],
    ['url', { url: 'https://evil.example/mark' }],
  ]) {
    r = await call({ ...good(), ...patch });
    assert.strictEqual(r.code, 400, name);
  }
  r = await call({ ...good(), kind: 'audio', reason: 'name' });
  assert.strictEqual(r.code, 200);
  console.log('ok  bad fields are refused; audio reasons only go with audio');

  assert.strictEqual((await call(good(), { origin: 'https://evil.example' })).code, 403);
  assert.strictEqual((await call(good(), { origin: null })).code, 403);
  assert.strictEqual((await call(good(), { method: 'GET' })).code, 405);
  assert.strictEqual((await call(JSON.stringify({ ...good(), note: 'x'.repeat(5000) }))).code, 413);
  assert.strictEqual((await call('{not json')).code, 400);
  console.log('ok  wrong origin, method, size and JSON are refused');

  const long = (await call({ ...good(), note: 'y'.repeat(900) })).code;
  assert.strictEqual(long, 200);
  assert.ok(calls.at(-1).body.body.includes('y'.repeat(500) + '\n~~~'), 'note capped at 500');
  console.log('ok  notes are capped at 500 characters');

  const codes = [];
  for (let i = 0; i < 7; i++) codes.push((await call(good(), { ip: '192.0.2.9' })).code);
  assert.deepStrictEqual(codes, [200, 200, 200, 200, 200, 429, 429]);
  console.log('ok  five reports per IP per ten minutes');

  process.env.REPORTS_DRY_RUN = '1'; calls = [];
  r = await call(good());
  assert.ok(r.j.dryRun && r.j.issue.title && calls.length === 0);
  delete process.env.REPORTS_DRY_RUN;
  delete process.env.REPORTS_TOKEN;
  assert.strictEqual((await call(good())).code, 503);
  console.log('ok  dry run, and 503 without a token');
  console.log('all passed');
})().catch((e) => { console.error(e); process.exit(1); });
