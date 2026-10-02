#!/usr/bin/env python3
"""Write the Read section: the home page (site/index.html, a book picker) and one thin
full-window reader page per book (site/read/<slug>/index.html). All the behaviour lives in
site/assets/present.js and present.css; these pages only say which book to load.

  python3 scripts/build_read_pages.py

Rerun after adding a book (add it to BOOKS below, in canonical order) or after its motion or
narration files appear: a page loads <book>-motion.js and <book>-audio.js only if they exist.
It also reports every scene that is missing motion or audio, or whose audio has the wrong verse count.
"""
import html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, 'site')
ASSET_V = 11  # bump when present.js or present.css change, so browsers fetch the new files
REPORT_V = 1  # bump when site/assets/report.js changes, and its ?v= on every book page too

# slug: (site folder, file prefix, short name, title, testament)
BOOKS = {
    'genesis': ('genesis', 'genesis', 'Genesis', 'Genesis', 'Old'),
    'ruth': ('ruth', 'ruth', 'Ruth', 'The Book of Ruth', 'Old'),
    '1samuel': ('1samuel', '1samuel', '1 Samuel', 'The First Book of Samuel', 'Old'),
    '2samuel': ('2samuel', '2samuel', '2 Samuel', 'The Second Book of Samuel', 'Old'),
    '1kings': ('1kings', '1kings', '1 Kings', 'The First Book of the Kings', 'Old'),
    '2kings': ('2kings', '2kings', '2 Kings', 'The Second Book of the Kings', 'Old'),
    '1chronicles': ('1chronicles', '1chronicles', '1 Chronicles', 'The First Book of the Chronicles', 'Old'),
    '2chronicles': ('2chronicles', '2chronicles', '2 Chronicles', 'The Second Book of the Chronicles', 'Old'),
    'ezra': ('ezra', 'ezra', 'Ezra', 'The Book of Ezra', 'Old'),
    'nehemiah': ('nehemiah', 'nehemiah', 'Nehemiah', 'The Book of Nehemiah', 'Old'),
    'esther': ('esther', 'esther', 'Esther', 'The Book of Esther', 'Old'),
    'matthew': ('matthew', 'matthew', 'Matthew', 'The Gospel of Matthew', 'New'),
    'mark': ('mark', 'mark', 'Mark', 'The Gospel of Mark', 'New'),
    'luke': ('luke', 'luke', 'Luke', 'The Gospel of Luke', 'New'),
    'john': ('bible', 'john', 'John', 'The Gospel of John', 'New'),
    'acts': ('acts', 'acts', 'Acts', 'The Acts of the Apostles', 'New'),
}
ONES = ('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen '
        'sixteen seventeen eighteen nineteen').split()
TENS = {2: 'twenty', 3: 'thirty', 4: 'forty', 5: 'fifty'}


def words(n):
    return ONES[n] if n < 20 else TENS[n // 10] + ('-' + ONES[n % 10] if n % 10 else '')


def chapters(folder, prefix):
    out = {}
    d = os.path.join(SITE, folder, 'data')
    for f in sorted(os.listdir(d)):
        m = re.fullmatch(re.escape(prefix) + r'-(\d\d)\.js', f)
        if m:
            t = open(os.path.join(d, f)).read()
            out[int(m.group(1))] = json.loads(t[t.index(',') + 1:t.rindex(')')])
    return out


def coverage(folder, prefix, chs):
    """Problems a reader would hit: scenes without motion or audio, or audio without one time per verse."""
    def load(name):
        p = os.path.join(SITE, folder, 'data', f'{prefix}-{name}.js')
        if not os.path.exists(p):
            return None
        t = open(p).read()
        return json.loads('\n'.join(l for l in t[t.index('{'):t.rindex('}') + 1].splitlines() if not l.startswith('//')))
    motion, audio, out = load('motion'), load('audio'), []
    for c, d in chs.items():
        for sc in d['scenes']:
            k = f'{c}:{sc[0]}'
            if motion is not None and k not in motion:
                out.append(f'{k} has no motion')
            if audio is not None:
                a = audio.get(k)
                if not a:
                    out.append(f'{k} has no audio')
                elif len(a['t']) != sc[1] - sc[0] + 1 or not os.path.exists(os.path.join(SITE, a['src'].split('?')[0].lstrip('/'))):
                    out.append(f'{k} audio does not match its verses or its file is missing')
    if motion is None:
        out.append('no motion file (build_motion.py)')
    if audio is None:
        out.append('no narration yet (build_audio.py)')
    return out


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp'
    open(tmp, 'w').write(text)
    os.replace(tmp, path)


HEAD = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#05060a">
<meta property="og:image" content="/infographic/og.png">
<link rel="icon" href="/assets/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Marcellus&family=Spectral:ital,wght@0,300;0,400;0,500;1,300;1,400&display=swap" rel="stylesheet">
'''


def reader_page(slug, folder, prefix, name, title, chs):
    n = len(chs)
    scenes = sum(len(c['scenes']) for c in chs.values())
    data = f'/{folder}/data/'
    tags = '\n'.join(f'<script src="{data}{prefix}-{c:02d}.js"></script>' for c in sorted(chs))
    for extra in ('motion', 'audio'):
        if os.path.exists(os.path.join(SITE, folder, 'data', f'{prefix}-{extra}.js')):
            tags += f'\n<script src="{data}{prefix}-{extra}.js"></script>'
    lede = (f'{words(n).capitalize()} chapter{"s" if n > 1 else ""}, one scene at a time. '
            'The picture fills the window while you read. King James Version.')
    config = json.dumps({'slug': slug, 'book': name, 'title': title, 'back': '/' + (folder if folder != 'bible' else 'bible'),
                         'lede': lede}, ensure_ascii=False)
    return (HEAD.format(title=f'Read {html.escape(name)}: a visual Bible',
                        desc=html.escape(f'{title} in the King James Version, {scenes} illustrated scenes, '
                                         'each picture filling the window as the passage is read.'))
            + f'<link rel="stylesheet" href="/assets/present.css?v={ASSET_V}">\n<script>\n'
            '  window.VB={ch:{},add:function(c,d){this.ch[c]=d;}};\n'
            f'  window.READ={config};\n</script>\n{tags}\n</head>\n<body>\n'
            f'<noscript><p style="padding:2rem">This page needs JavaScript. <a href="/{folder}" style="color:#d4b066">'
            f'See all scenes in {html.escape(name)}</a>.</p></noscript>\n'
            f'<script src="/assets/report.js?v={REPORT_V}"></script>\n'
            f'<script src="/assets/present.js?v={ASSET_V}"></script>\n</body>\n</html>\n')


def nav():
    groups = {'Old': [], 'New': []}
    for slug, (folder, _, name, _, t) in BOOKS.items():
        groups[t].append(f'      <a class="link" href="/read/{slug}">{html.escape(name)}</a>')
    return ('<nav class="sitenav over" aria-label="Site">\n'
            '  <a class="brand" href="/" aria-current="page">halo <b>·</b> Visual Bible</a>\n'
            '  <a class="link" href="/story">The story</a>\n'
            '  <details class="books">\n    <summary>Books</summary>\n    <div class="menu" aria-label="Books">\n'
            '      <span class="group">Old Testament</span>\n' + '\n'.join(groups['Old']) + '\n'
            '      <span class="group">New Testament</span>\n' + '\n'.join(groups['New']) + '\n'
            '    </div>\n  </details>\n'
            '  <a class="link" href="/making-of">Making of</a>\n'
            '  <a class="link" href="/under-the-hood">Under the hood</a>\n'
            '  <a class="link" href="https://github.com/btrzupek/halo-visual-bible">GitHub</a>\n</nav>\n'
            '<script src="/assets/nav.js?v=2" defer></script>\n')


def home(books):
    total = sum(b['scenes'] for b in books)
    cards = {'Old': [], 'New': []}
    for b in books:
        voiced = ' · narrated' if b['audio'] else ''
        cards[b['testament']].append(
            f'<a class="book" href="/read/{b["slug"]}"><img src="/images/full/{b["img"]}" alt="" loading="lazy">'
            f'<span class="name">{html.escape(b["name"])}</span>'
            f'<span class="meta">{b["chapters"]} chapters · {b["scenes"]} scenes{voiced}</span></a>')
    hero = books[0]['img']
    return (HEAD.format(title='The Visual Bible', desc=html.escape(
                f'The King James Bible, one scene at a time: {len(books)} books and {total} illustrated scenes, '
                'each read aloud, all made locally on an AMD Ryzen AI Halo box.'))
            + '<link rel="stylesheet" href="/assets/site.css?v=back1">\n<style>\n'
            ':root{--ink:#efe6d0;--soft:#cbbf9f;--gilt:#d4b066;--serif:"Spectral",Georgia,serif;--display:"Marcellus",Georgia,serif}\n'
            '*{box-sizing:border-box}\n'
            'body{margin:0;min-height:100svh;background:#05060a;color:var(--ink);font-family:var(--serif);-webkit-font-smoothing:antialiased}\n'
            '.hero{position:relative;min-height:88svh;display:grid;align-items:end;overflow:hidden}\n'
            '.hero img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.8;animation:dawn 3.2s ease-out both}\n'
            '.hero::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(5,6,10,.2) 30%,#05060a 100%)}\n'
            '@keyframes dawn{from{opacity:0;transform:scale(1.05)}}\n'
            '.hero .inner{position:relative;z-index:1;padding:0 clamp(1.25rem,6vw,5rem) clamp(2rem,7vh,4rem);max-width:62rem}\n'
            '.hero h1{font-family:var(--display);font-weight:400;font-size:clamp(2.8rem,8vw,6.4rem);line-height:1;margin:0 0 1rem}\n'
            '.hero p{color:var(--soft);font-style:italic;font-size:1.1rem;margin:0 0 1.8rem;max-width:44ch}\n'
            '.go{display:flex;flex-wrap:wrap;gap:.8rem}\n'
            '.go a{font-family:var(--display);font-size:1.05rem;letter-spacing:.04em;border-radius:999px;padding:.75rem 1.5rem;text-decoration:none}\n'
            '.go .primary{background:var(--gilt);color:#14110a}.go .primary:hover{background:#e2c27e}\n'
            '.go .ghost{border:1px solid rgba(239,230,208,.35);color:var(--ink)}.go .ghost:hover{border-color:var(--ink)}\n'
            '.go[hidden]{display:none}\n'
            'section{padding:0 clamp(1.25rem,6vw,5rem) 3rem}\n'
            'section h2{font-family:var(--display);font-weight:400;font-size:1.05rem;letter-spacing:.14em;text-transform:uppercase;color:var(--gilt);'
            'margin:2.5rem 0 1.2rem;display:flex;align-items:center;gap:1rem}\n'
            'section h2::after{content:"";flex:1;height:1px;background:rgba(212,176,102,.25)}\n'
            'section .books{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,19rem),1fr));gap:1.1rem}\n'
            '.book{position:relative;display:block;aspect-ratio:16/9;overflow:hidden;border-radius:4px;color:var(--ink);text-decoration:none;background:#111}\n'
            '.book img{width:100%;height:100%;object-fit:cover;transition:transform 6s ease}\n'
            '.book:hover img{transform:scale(1.07)}\n'
            '.book::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,transparent 40%,rgba(5,6,10,.88))}\n'
            '.book .name{position:absolute;z-index:1;left:1.1rem;bottom:2.1rem;font-family:var(--display);font-size:1.6rem}\n'
            '.book .meta{position:absolute;z-index:1;left:1.1rem;bottom:.9rem;font-style:italic;font-size:.92rem;color:var(--soft)}\n'
            'footer{padding:2rem clamp(1.25rem,6vw,5rem) 3rem;color:var(--soft);font-size:.95rem;max-width:70ch}\n'
            'footer a{color:var(--gilt)}\n'
            '@media (prefers-reduced-motion:reduce){.hero img{animation:none}.book img{transition:none}}\n'
            '</style>\n</head>\n<body>\n' + nav()
            + f'<header class="hero"><img src="/images/full/{hero}" alt="">\n<div class="inner">\n'
            '<h1>The Visual Bible</h1>\n'
            '<p>The King James Bible, one scene at a time. Each picture fills the screen while the passage is read aloud.</p>\n'
            '<div class="go" id="go"><a class="primary" href="/read/genesis">Begin with Genesis</a>'
            '<a class="ghost" href="/read/john">Begin with John</a></div>\n</div></header>\n'
            '<section aria-label="Old Testament"><h2>Old Testament</h2><div class="books">' + ''.join(cards['Old']) + '</div></section>\n'
            '<section aria-label="New Testament"><h2>New Testament</h2><div class="books">' + ''.join(cards['New']) + '</div></section>\n'
            '<footer><p>Every picture was generated, and every word read aloud, on one AMD Ryzen AI Halo computer on my desk. '
            'Scripture is the King James Version, which is in the public domain.</p>'
            '<p><a href="/story">Read how this was made</a> · <a href="/making-of">see every attempt</a> · '
            '<a href="/under-the-hood">code and numbers</a></p></footer>\n'
            '<script>\n// "Continue" where the reader left off (stored by present.js)\n'
            'try{var l=JSON.parse(localStorage.getItem("read-last")||"null");if(l&&l.slug){var g=document.getElementById("go");'
            'g.innerHTML=\'<a class="primary" href="/read/\'+l.slug+\'#\'+l.id+\'">Continue \'+l.ref.replace(/[<&]/g,"")+\'</a>\'+'
            '\'<a class="ghost" href="/read/genesis">Begin with Genesis</a>\';}}catch(e){}\n</script>\n</body>\n</html>\n')


def main():
    books = []
    for slug, (folder, prefix, name, title, testament) in BOOKS.items():
        chs = chapters(folder, prefix)
        write(os.path.join(SITE, 'read', slug, 'index.html'), reader_page(slug, folder, prefix, name, title, chs))
        books.append({'slug': slug, 'name': name, 'testament': testament, 'chapters': len(chs),
                      'scenes': sum(len(c['scenes']) for c in chs.values()),
                      'img': chs[min(chs)]['scenes'][0][2].replace('.png', '.webp'),
                      'audio': os.path.exists(os.path.join(SITE, folder, 'data', f'{prefix}-audio.js'))})
        problems = coverage(folder, prefix, chs)
        print(f'/read/{slug}: {books[-1]["chapters"]} chapters, {books[-1]["scenes"]} scenes, '
              + ('complete' if not problems else f'{len(problems)} problem(s): ' + '; '.join(problems[:5])))
    write(os.path.join(SITE, 'index.html'), home(books))
    print('home: site/index.html')


if __name__ == '__main__':
    main()
