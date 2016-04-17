"""raw/posts.json (WordPress REST) -> content/posts/{id}.md
Crayon code blocks -> fenced code; common tags -> markdown; the rest stays HTML (goldmark unsafe)."""
import html, json, re
from pathlib import Path

cats = {c['id']: c['name'] for c in json.load(open('raw/categories.json', encoding='utf-8'))}
tags = {t['id']: t['name'] for t in json.load(open('raw/tags.json', encoding='utf-8'))}

CRAYON = re.compile(r'<!-- Crayon Syntax Highlighter.*?<!-- \[Format Time:[^\]]*\] -->', re.S)
LANG = {'c++': 'cpp', 'c#': 'csharp', 'default': ''}

def crayon(m):
    block = m.group(0)
    lang = re.search(r'class="crayon-language">([^<]*)<', block)
    lang = (lang.group(1) if lang else '').strip().lower()
    code = re.search(r'<textarea[^>]*class="crayon-plain[^>]*>(.*?)</textarea>', block, re.S).group(1)
    return f"\n\n```{LANG.get(lang, lang)}\n{html.unescape(code).strip()}\n```\n\n"

def inline(s):
    s = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', r'[\2](\1)', s, flags=re.S)
    s = re.sub(r'<(strong|b)>(.*?)</\1>', r'**\2**', s, flags=re.S)
    s = re.sub(r'<(em|i)>(.*?)</\1>', r'*\2*', s, flags=re.S)
    s = re.sub(r'<code>(.*?)</code>', r'`\1`', s, flags=re.S)
    s = re.sub(r'<img [^>]*src="([^"]+)"[^>]*/?>', img, s)
    s = re.sub(r'<br\s*/?>', '  \n', s)
    s = re.sub(r'<span[^>]*>|</span>', '', s)
    return s

def img(m):
    src = re.sub(r'^https?://yonmy\.com/wp-content/uploads/', '', m.group(1))
    src = re.sub(r'-\d+x\d+(\.\w+)$', r'\1', src)  # thumbnail -> original
    return f'![]({"/images/" + src})'

def convert(h):
    h = h.replace('\r\n', '\n')
    parts = CRAYON.split(h)
    codes = [crayon(m) for m in CRAYON.finditer(h)]
    out = []
    for i, part in enumerate(parts):
        out.append(prose(part))
        if i < len(codes):
            out.append(codes[i])
    md = ''.join(out)
    md = re.sub(r'\n{3,}', '\n\n', md).strip() + '\n'
    return md

def prose(s):
    s = re.sub(r'<h(\d)[^>]*>(.*?)</h\1>', lambda m: f"\n\n{'#' * int(m.group(1))} {m.group(2).strip()}\n\n", s, flags=re.S)
    s = re.sub(r'<blockquote>\s*<p>(.*?)</p>\s*</blockquote>', r'\n\n> \1\n\n', s, flags=re.S)
    s = re.sub(r'<hr\s*/?>', '\n\n---\n\n', s)
    while re.search(r'<(ul|ol)>', s):  # innermost lists first
        s = re.sub(r'<(ul|ol)>((?:(?!<ul>|<ol>).)*?)</\1>', lst, s, flags=re.S)
    s = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\n\1\n\n', s, flags=re.S)
    return html.unescape(inline(s)) if '<table' not in s else inline(s)

def lst(m):
    bullet = '- ' if m.group(1) == 'ul' else '1. '
    lines = []
    for it in re.findall(r'<li>(.*?)</li>', m.group(2), re.S):
        head, *rest = it.strip().split('\n\n', 1)  # rest = already-converted nested list
        lines.append(bullet + head.strip())
        if rest:
            lines += ['  ' + l for l in rest[0].strip().split('\n')]
    return '\n\n' + '\n'.join(lines) + '\n\n'

def yq(s):  # yaml quoted string
    return json.dumps(s, ensure_ascii=False)

for p in json.load(open('raw/posts.json', encoding='utf-8')):
    fm = [
        f"title: {yq(html.unescape(p['title']['rendered']))}",
        f"date: {p['date']}+09:00",
        f"url: /archives/{p['id']}/",
        f"categories: [{', '.join(yq(cats[c]) for c in p['categories'])}]",
        f"tags: [{', '.join(yq(tags[t]) for t in p['tags'])}]",
    ]
    body = convert(p['content']['rendered'])
    Path(f"content/posts/{p['id']}.md").write_text('---\n' + '\n'.join(fm) + '\n---\n\n' + body, encoding='utf-8', newline='\n')
    assert body.count('```') % 2 == 0 and body.count('```') // 2 == len(CRAYON.findall(p['content']['rendered'])), p['id']
    assert 'crayon' not in body, p['id']
print('ok')
