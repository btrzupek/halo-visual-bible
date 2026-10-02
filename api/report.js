// /api/report: a reader flags a problem with a scene's picture or narration (site/assets/report.js).
// The report is checked here and filed as an issue in a private GitHub repo; a second report of the
// same scene, kind and reason becomes a comment on the open issue instead of a new one.
// Nothing personal is kept: no IP, no cookies, no account. The rate limit holds a salted hash of
// the IP in memory for ten minutes and never writes it anywhere.
//
// Vercel environment variables:
//   REPORTS_TOKEN    fine-grained token with Issues: read and write on REPORTS_REPO only
//   REPORTS_REPO     owner/name, default btrzupek/halo-visual-bible-reports
//   REPORTS_DRY_RUN  1 = return the issue that would be filed instead of filing it (local tests)
const crypto = require('crypto');

const BOOKS = {
  genesis: 'Genesis', ruth: 'Ruth', '1samuel': '1 Samuel', '2samuel': '2 Samuel', '1kings': '1 Kings', '2kings': '2 Kings',
  '1chronicles': '1 Chronicles', '2chronicles': '2 Chronicles', ezra: 'Ezra', nehemiah: 'Nehemiah', esther: 'Esther', matthew: 'Matthew', mark: 'Mark', luke: 'Luke',
  john: 'John', acts: 'Acts',
};
const REASONS = {
  image: {
    limbs: 'extra or missing limbs, hands or fingers', body: 'a distorted face or body',
    modern: 'a modern object', text: 'does not match the passage', history: 'theologically or historically wrong',
    modesty: 'immodest or too violent', other: 'something else',
  },
  audio: {
    name: 'a name is mispronounced', word: 'a word is misread, skipped or repeated',
    glitch: 'a glitch, noise or cut-off', sync: 'the highlighted verse is out of step', other: 'something else',
  },
};
const NOTE_MAX = 500, BODY_MAX = 4000, MIN_MS = 2500;
const WINDOW_MS = 10 * 60e3, PER_IP = 5, PER_INSTANCE = 60;
const SALT = crypto.randomBytes(16).toString('hex');  // per instance, so the hashes mean nothing elsewhere
const seen = new Map();  // hash -> [timestamps]
let recent = [];         // every accepted report on this instance, for the overall cap

function limited(ip, now) {
  recent = recent.filter((t) => now - t < WINDOW_MS);
  for (const [k, v] of seen) { const w = v.filter((t) => now - t < WINDOW_MS); if (w.length) seen.set(k, w); else seen.delete(k); }
  const key = crypto.createHash('sha256').update(SALT + ip).digest('hex').slice(0, 16);
  const mine = seen.get(key) || [];
  if (mine.length >= PER_IP || recent.length >= PER_INSTANCE) return true;
  mine.push(now); seen.set(key, mine); recent.push(now);
  return false;
}

const int = (n, lo, hi) => Number.isInteger(n) && n >= lo && n <= hi;

// Returns {error} or the cleaned report. Only fields we know, in shapes we expect.
function check(b, host) {
  if (!b || typeof b !== 'object') return { error: 'bad request' };
  const book = BOOKS[b.slug];
  if (!book) return { error: 'unknown book' };
  if (!int(b.chapter, 1, 150) || !int(b.verse, 1, 200) || !int(b.last, b.verse, 200)) return { error: 'bad verse' };
  if (!REASONS[b.kind] || !REASONS[b.kind][b.reason]) return { error: 'bad reason' };
  if (typeof b.file !== 'string' || !/^[A-Za-z0-9_-]{1,80}\.png$/.test(b.file)) return { error: 'bad image' };
  const audio = b.audio == null ? null : String(b.audio);
  if (audio && !/^\/audio\/[a-z0-9]+\/[A-Za-z0-9._-]{1,80}\.(mp3|m4a|ogg|opus|wav)(\?v=[A-Za-z0-9]{1,16})?$/.test(audio)) return { error: 'bad audio' };
  let url;
  try { url = new URL(String(b.url)); } catch (e) { return { error: 'bad url' }; }
  if (url.host !== host || !/^https?:$/.test(url.protocol)) return { error: 'bad url' };
  const note = String(b.note == null ? '' : b.note)
    .replace(/\r\n?/g, '\n').replace(/[\u0000-\u0008\u000b-\u001f\u007f​-‏‪-‮⁦-⁩]/g, '')
    .replace(/\n{3,}/g, '\n\n').trim().slice(0, NOTE_MAX);
  return {
    slug: b.slug, book, chapter: b.chapter, verse: b.verse, last: b.last, scene: `${b.slug}.${b.chapter}.${b.verse}`,
    file: b.file, audio, kind: b.kind, reason: b.reason, reasonText: REASONS[b.kind][b.reason], note,
    url: url.origin + url.pathname + url.hash.slice(0, 40), origin: url.origin,
  };
}

function issueFor(r) {
  const ref = `${r.book} ${r.chapter}:${r.verse}${r.last > r.verse ? '–' + r.last : ''}`;
  const what = r.kind === 'image' ? 'picture' : 'narration';
  const rows = [
    ['Book', r.book], ['Chapter', r.chapter], ['Scene', '`' + r.scene + '` (' + ref + ')'],
    ['Image', '`' + r.file + '`'], ...(r.audio ? [['Audio', '`' + r.audio + '`']] : []),
    ['Problem', `${what}: ${r.reasonText}`], ['Page', r.url],
  ];
  return {
    title: `${r.scene} ${what}: ${r.reasonText} (${ref})`,
    body: '| | |\n|---|---|\n' + rows.map(([k, v]) => `| ${k} | ${v} |`).join('\n') + '\n\n' +
      `![${r.scene}](${r.origin}/images/full/${r.file.replace(/\.png$/, '.webp')})\n\n` + noteBlock(r),
    labels: ['reader-report', r.kind, 'book:' + r.slug],
  };
}
// the note goes in a fenced block, so nothing in it renders as a link, an image or an @mention
function noteBlock(r) {
  return r.note ? 'Reader note:\n\n~~~text\n' + r.note.replace(/~{3,}/g, '~ ~ ~') + '\n~~~\n' : '_No note._\n';
}

async function gh(path, opts = {}) {
  const res = await fetch('https://api.github.com' + path, {
    ...opts,
    headers: {
      Authorization: 'Bearer ' + process.env.REPORTS_TOKEN, Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'halo-visual-bible-reports',
      ...(opts.body ? { 'Content-Type': 'application/json' } : {}),
    },
  });
  if (!res.ok) { const e = new Error('github ' + res.status); e.status = res.status; throw e; }
  return res.json();
}

async function file(r) {
  const repo = process.env.REPORTS_REPO || 'btrzupek/halo-visual-bible-reports';
  const issue = issueFor(r);
  // same scene, kind and reason already open: add to it instead (search lags a little; a rare duplicate is fine)
  try {
    const q = encodeURIComponent(`repo:${repo} is:issue is:open in:title "${r.scene}"`);
    const found = (await gh(`/search/issues?q=${q}&per_page=30`)).items.find((i) => i.title === issue.title);
    if (found) {
      await gh(`/repos/${repo}/issues/${found.number}/comments`, { method: 'POST',
        body: JSON.stringify({ body: `Another reader reported this.\n\nPage: ${r.url}\n\n` + noteBlock(r) }) });
      return { number: found.number, added: true };
    }
  } catch (e) { /* fall through and open a new issue */ }
  try {
    const made = await gh(`/repos/${repo}/issues`, { method: 'POST', body: JSON.stringify(issue) });
    return { number: made.number, added: false };
  } catch (e) {
    if (e.status !== 422) throw e;  // a label problem: file it without labels rather than lose it
    const made = await gh(`/repos/${repo}/issues`, { method: 'POST', body: JSON.stringify({ title: issue.title, body: issue.body }) });
    return { number: made.number, added: false };
  }
}

module.exports = async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') { res.setHeader('Allow', 'POST'); return res.status(405).json({ error: 'POST only' }); }
  const host = req.headers.host;
  const origin = req.headers.origin;
  try { if (!origin || new URL(origin).host !== host) return res.status(403).json({ error: 'forbidden' }); }
  catch (e) { return res.status(403).json({ error: 'forbidden' }); }

  let b = req.body;
  if (typeof b === 'string') {
    if (b.length > BODY_MAX) return res.status(413).json({ error: 'too large' });
    try { b = JSON.parse(b); } catch (e) { return res.status(400).json({ error: 'bad request' }); }
  } else if (b && JSON.stringify(b).length > BODY_MAX) return res.status(413).json({ error: 'too large' });

  // bots: the hidden field filled in, or sent faster than a person could. Answer as if it worked.
  if (!b || b.website || !(Number(b.t) >= MIN_MS)) return res.status(200).json({ ok: true });

  const r = check(b, host);
  if (r.error) return res.status(400).json({ error: r.error });

  const ip = String(req.headers['x-forwarded-for'] || '').split(',')[0].trim() || (req.socket && req.socket.remoteAddress) || '';
  if (limited(ip, Date.now())) return res.status(429).json({ error: 'too many reports' });

  if (process.env.REPORTS_DRY_RUN === '1') return res.status(200).json({ ok: true, dryRun: true, issue: issueFor(r) });
  if (!process.env.REPORTS_TOKEN) return res.status(503).json({ error: 'Reports are not switched on yet.' });
  try {
    const out = await file(r);
    return res.status(200).json({ ok: true, added: out.added });
  } catch (e) {
    console.error('report failed', e.status || e.message);
    return res.status(502).json({ error: 'Sorry, the report could not be filed. Please try again later.' });
  }
};
module.exports._test = { check, issueFor, limited, BOOKS, REASONS };
