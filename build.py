#!/usr/bin/env python3
"""Build the web edition of The Last Normal Week.

Reads story/ (series.json, season-NN/season.json, season-NN/episode-NN/episode.json
and chapter Markdown files) and writes a static site to site/.

Standard library only. Run:  python3 build.py
"""

import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parent
STORY = ROOT / "story"
OUT = ROOT / "site"

SERIES_THEME = {
    "fonts": {"display": "Big Shoulders Display", "display_weights": "600;800",
              "body": "Newsreader", "ui": "IBM Plex Mono"},
    "palette": {
        "light": {"bg": "#ECEDEE", "paper": "#F6F6F5", "fg": "#141516", "muted": "#5E6266",
                  "accent": "#C9352A", "rule": "#D3D5D7", "screen": "#FFFFFF"},
        "dark": {"bg": "#0D0E0F", "paper": "#141516", "fg": "#E6E6E4", "muted": "#8F9397",
                 "accent": "#FF5E4F", "rule": "#26282B", "screen": "#1B1D20"},
    },
}


# ---------------------------------------------------------------- loading

def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def parse_chapter(path):
    text = path.read_text(encoding="utf-8")
    meta = {}
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.split("#", 1)[0].strip()
        text = text[m.end():]
    slug = path.stem
    num = int(slug.split("-", 1)[0])
    words = len(re.findall(r"[A-Za-z0-9’']+", text))
    return {"meta": meta, "body": text, "slug": slug, "num": num, "words": words}


def load_story():
    series = load_json(STORY / "series.json")
    seasons = []
    for sdir in sorted(STORY.glob("season-*")):
        season = load_json(sdir / "season.json")
        season["dir"] = sdir.name
        season["episodes"] = []
        for edir in sorted(sdir.glob("episode-*")):
            ep = load_json(edir / "episode.json")
            ep["dir"] = edir.name
            ep["chapters"] = [parse_chapter(p) for p in sorted(edir.glob("[0-9]*.md"))]
            season["episodes"].append(ep)
        seasons.append(season)
    return series, seasons


# ---------------------------------------------------------------- prose → HTML

def smart_quotes(s):
    s = re.sub(r'(^|[\s(\[—–-])"', "\\1“", s)
    s = s.replace('"', "”")
    s = re.sub(r"(^|[\s(\[—–-])'", "\\1‘", s)
    s = s.replace("'", "’")
    return s


def inline(s):
    s = html.escape(s, quote=False)
    s = smart_quotes(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\](?!\()", r'<span class="tr">[\1]</span>', s)
    return s


def render_screen(lines):
    out = ['<div class="screen" role="group">']
    for line in lines:
        m = re.match(r"\*\*([^*]+?):\*\*\s*(.*)$", line)
        if m:
            out.append(f'<p class="msg"><span class="from">{inline(m.group(1))}</span>'
                       f'<span class="txt">{inline(m.group(2))}</span></p>')
        else:
            out.append(f'<p class="msg">{inline(line)}</p>')
    out.append("</div>")
    return "\n".join(out)


def render_body(text):
    blocks = re.split(r"\n\s*\n", text.strip())
    out = []
    for block in blocks:
        lines = [l.rstrip() for l in block.strip().splitlines()]
        if not lines:
            continue
        if lines == ["* * *"]:
            out.append('<hr class="break" aria-label="Section break">')
        elif all(l.startswith(">") for l in lines):
            out.append(render_screen([l[1:].strip() for l in lines]))
        else:
            out.append(f"<p>{inline(' '.join(lines))}</p>")
    return "\n".join(out)


# ---------------------------------------------------------------- theming

def fonts_link(fonts):
    fams = [f"family={quote_plus(fonts['display'])}:wght@{fonts.get('display_weights', '700')}",
            f"family={quote_plus(fonts['body'])}:ital,opsz,wght@0,6..72,400;0,6..72,600;1,6..72,400",
            f"family={quote_plus(fonts['ui'])}:wght@400;500"]
    return ("<link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">"
            "<link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>"
            f"<link rel=\"stylesheet\" href=\"https://fonts.googleapis.com/css2?{'&'.join(fams)}&display=swap\">")


def theme_css(theme):
    def tokens(p):
        return "".join(f"--{k}:{v};" for k, v in p.items())
    f = theme["fonts"]
    light, dark = theme["palette"]["light"], theme["palette"]["dark"]
    return (
        f":root{{{tokens(light)}"
        f"--display:'{f['display']}',Impact,'Arial Narrow',sans-serif;"
        f"--body:'{f['body']}',Georgia,'Times New Roman',serif;"
        f"--ui:'{f['ui']}',ui-monospace,Menlo,Consolas,monospace;color-scheme:light}}"
        f"@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{{tokens(dark)}color-scheme:dark}}}}"
        f":root[data-theme=dark]{{{tokens(dark)}color-scheme:dark}}"
    )


BASE_CSS = """
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:400 1.125rem/1.7 var(--body);
  font-optical-sizing:auto;text-rendering:optimizeLegibility}
a{color:inherit}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
.wrap{width:100%;max-width:44rem;margin:0 auto;
  padding-left:max(20px,env(safe-area-inset-left,0px));padding-right:max(20px,env(safe-area-inset-right,0px))}
.wide{max-width:64rem}
.bar{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--rule)}
.bar .wrap{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding-block:.7rem;
  font:500 .72rem/1.3 var(--ui);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.bar a{text-decoration:none}
.bar a:hover{color:var(--fg)}
.bar .series{color:var(--fg);font:800 1rem/1 var(--display);letter-spacing:.06em}
.progress{position:absolute;left:0;bottom:-1px;height:2px;width:0;background:var(--accent)}
.eyebrow{font:500 .75rem/1.4 var(--ui);letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.eyebrow b{color:var(--accent);font-weight:500}
h1,h2,h3{font-family:var(--display);font-weight:800;text-transform:uppercase;letter-spacing:.02em;
  line-height:.95;text-wrap:balance;margin:0}
/* chapter */
.chapter-head{padding-block:clamp(3rem,10vw,6rem) 2.5rem}
.chapter-head h1{font-size:clamp(3rem,11vw,5.5rem);margin:.6rem 0 1.4rem}
.meta{display:flex;flex-wrap:wrap;gap:.35rem 1.25rem;font:400 .8rem/1.5 var(--ui);color:var(--muted)}
.meta span{white-space:nowrap}
.meta .pov{color:var(--fg)}
.prose{padding-bottom:3rem}
.prose p{margin:0 0 1.1em}
.prose em{font-style:italic}
.tr{font-size:.86em;color:var(--muted);white-space:nowrap}
hr.break{border:0;height:1.5rem;margin:2.2rem 0;text-align:center;overflow:visible}
hr.break::before{content:"···";font:400 1.2rem/1 var(--ui);letter-spacing:.6em;color:var(--accent)}
.screen{margin:1.6rem 0 1.8rem;padding:.9rem 1.1rem;background:var(--screen);border:1px solid var(--rule);
  border-radius:14px;font:400 .86rem/1.5 var(--ui);display:grid;gap:.45rem;max-width:34rem;
  box-shadow:0 1px 0 var(--rule)}
.screen .msg{margin:0;display:flex;flex-wrap:wrap;gap:.15rem .6rem;min-width:0;overflow-wrap:anywhere}
.screen .from{color:var(--accent);font-weight:500}
.screen strong{font-weight:500}
.pager{display:grid;grid-template-columns:1fr 1fr;gap:1rem;padding-block:2rem 4rem;border-top:1px solid var(--rule)}
.pager a{display:block;text-decoration:none;padding:1rem 0;min-width:0}
.pager .dir{font:500 .72rem/1.4 var(--ui);letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.pager .t{display:block;font:800 1.5rem/1 var(--display);text-transform:uppercase;margin-top:.4rem}
.pager a:hover .t{color:var(--accent)}
.pager .next{text-align:right;grid-column:2}
/* episode + series */
.cover{padding-block:clamp(3rem,10vw,7rem) 2rem}
.cover h1{font-size:clamp(3.4rem,13vw,7.5rem);margin:.8rem 0 1.5rem}
.lede{font-size:1.25rem;line-height:1.6;max-width:36rem;margin:0 0 1rem}
.mood{font:400 .82rem/1.6 var(--ui);color:var(--muted);max-width:34rem}
.toc{list-style:none;margin:2rem 0 5rem;padding:0;border-top:1px solid var(--fg)}
.toc li{border-bottom:1px solid var(--rule)}
.toc a{display:grid;grid-template-columns:3rem 1fr;gap:.25rem 1rem;padding:1.1rem 0;text-decoration:none}
.toc .n{font:500 .8rem/1.9 var(--ui);color:var(--accent);font-variant-numeric:tabular-nums}
.toc .t{font:800 clamp(1.5rem,5vw,2.1rem)/1 var(--display);text-transform:uppercase}
.toc a:hover .t{color:var(--accent)}
.toc .d{grid-column:2;font:400 .78rem/1.5 var(--ui);color:var(--muted)}
.season{margin:2.5rem 0 5rem}
.season h2{font-size:1.6rem;margin:0 0 .3rem}
.eps{display:grid;gap:1rem;margin-top:1.5rem;grid-template-columns:repeat(auto-fill,minmax(min(100%,19rem),1fr))}
.ep{--ep-bg:var(--l-bg);--ep-fg:var(--l-fg);--ep-accent:var(--l-accent);display:flex;flex-direction:column;gap:.6rem;padding:1.4rem;text-decoration:none;border-radius:4px;
  background:var(--ep-bg);color:var(--ep-fg);min-height:15rem;border:1px solid var(--rule)}
.ep .k{font:500 .72rem/1.4 var(--ui);letter-spacing:.1em;text-transform:uppercase;color:var(--ep-accent)}
.ep .t{font:800 2.2rem/.95 var(--ep-display);text-transform:uppercase}
.ep .s{font:400 .95rem/1.55 var(--body);opacity:.85;margin-top:auto}
.ep:hover{outline:2px solid var(--ep-accent);outline-offset:2px}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .ep{--ep-bg:var(--d-bg);--ep-fg:var(--d-fg);--ep-accent:var(--d-accent)}}
:root[data-theme=dark] .ep{--ep-bg:var(--d-bg);--ep-fg:var(--d-fg);--ep-accent:var(--d-accent)}
.soon{color:var(--muted);font:400 .82rem/1.6 var(--ui);margin-top:1rem}
footer{border-top:1px solid var(--rule);padding-block:1.5rem 2.5rem;font:400 .75rem/1.6 var(--ui);color:var(--muted)}
footer .wrap{display:flex;flex-wrap:wrap;gap:.5rem 1.5rem;justify-content:space-between}
@media (prefers-reduced-motion:no-preference){.prose,.cover,.chapter-head{animation:in .5s ease both}}
@keyframes in{from{opacity:.001;transform:translateY(6px)}to{opacity:1;transform:none}}
"""

PROGRESS_JS = """
<script>
(function(){var b=document.querySelector('.progress');if(b){var f=function(){var h=document.documentElement;
var m=h.scrollHeight-h.clientHeight;b.style.width=(m>0?Math.min(100,h.scrollTop/m*100):0)+'%'};
addEventListener('scroll',f,{passive:true});f()}
var p=document.querySelector('a[rel=prev]'),n=document.querySelector('a[rel=next]');
addEventListener('keydown',function(e){if(e.altKey||e.ctrlKey||e.metaKey)return;
if(e.key==='ArrowLeft'&&p)location.href=p.href;if(e.key==='ArrowRight'&&n)location.href=n.href})})();
</script>"""


def page(title, theme, body, description, depth, extra_head=""):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
{fonts_link(theme['fonts'])}
<link rel="stylesheet" href="{'../' * depth}base.css">
<style>{theme_css(theme)}</style>
{extra_head}
</head>
<body>
{body}
{PROGRESS_JS}
</body>
</html>
"""


def footer(series):
    return (f'<footer><div class="wrap wide"><span>Written by '
            f'<a href="{series["author_url"]}">{html.escape(series["author"])}</a></span>'
            f'<span>A work of fiction. Names, characters and events are invented.</span></div></footer>')


def ep_code(season, ep):
    return f"S{season['number']} · E{ep['number']}"


# ---------------------------------------------------------------- pages

def build_chapter(series, season, ep, idx, flat, pos):
    ch = ep["chapters"][idx]
    m = ch["meta"]
    pov = m.get("pov", "none")
    pov_txt = "" if pov == "none" else f'<span class="pov">{html.escape(pov)}</span>'
    prev_ = flat[pos - 1] if pos > 0 else None
    next_ = flat[pos + 1] if pos + 1 < len(flat) else None

    def link(item, rel):
        if not item:
            return '<span></span>'
        s, e, c = item
        href = f"../../{s['dir']}/{e['dir']}/{c['slug']}.html"
        label = "Previous" if rel == "prev" else "Next"
        if e is not ep:
            label += f" · {ep_code(s, e)}"
        cls = "next" if rel == "next" else "prev"
        return (f'<a class="{cls}" rel="{rel}" href="{href}"><span class="dir">{label}</span>'
                f'<span class="t">{html.escape(c["meta"]["title"])}</span></a>')

    body = f"""
<header class="bar"><div class="wrap">
<a class="series" href="../../index.html">{html.escape(series['title'])}</a>
<a href="index.html">{ep_code(season, ep)} · {idx + 1}/{len(ep['chapters'])}</a>
</div><div class="progress"></div></header>
<main>
<div class="wrap chapter-head">
<p class="eyebrow"><b>Chapter {ch['num']}</b> · {html.escape(ep['title'])}</p>
<h1>{html.escape(m.get('title', ''))}</h1>
<div class="meta">{pov_txt}<span>{html.escape(m.get('date', ''))}</span><span>{html.escape(m.get('place', ''))}</span></div>
</div>
<article class="wrap prose">
{render_body(ch['body'])}
</article>
<nav class="wrap pager" aria-label="Chapters">{link(prev_, 'prev')}{link(next_, 'next')}</nav>
</main>
{footer(series)}"""
    desc = f"{ep_code(season, ep)}, chapter {ch['num']} of {series['title']}."
    return page(f"{m.get('title')} · {series['title']}", ep, body, desc, depth=2)


def build_episode(series, season, ep):
    items = []
    for ch in ep["chapters"]:
        m = ch["meta"]
        pov = m.get("pov", "none")
        who = "" if pov == "none" else f"{pov} · "
        items.append(f'<li><a href="{ch["slug"]}.html"><span class="n">{ch["num"]:02d}</span>'
                     f'<span class="t">{html.escape(m["title"])}</span>'
                     f'<span class="d">{html.escape(who + m.get("date", ""))}</span></a></li>')
    words = sum(c["words"] for c in ep["chapters"])
    body = f"""
<header class="bar"><div class="wrap">
<a class="series" href="../../index.html">{html.escape(series['title'])}</a>
<span>Season {season['number']} · {html.escape(season['title'])}</span>
</div></header>
<main class="wrap">
<section class="cover">
<p class="eyebrow"><b>Episode {ep['number']}</b> · {html.escape(ep['dates'])}</p>
<h1>{html.escape(ep['title'])}</h1>
<p class="lede">{html.escape(ep['summary'])}</p>
<p class="mood">{len(ep['chapters'])} chapters · about {round(words, -2):,} words · {round(words / 230)} min read</p>
</section>
<ol class="toc">{''.join(items)}</ol>
</main>
{footer(series)}"""
    return page(f"{ep['title']} · {series['title']}", ep, body, ep["summary"], depth=2)


def build_index(series, seasons):
    blocks = []
    for s in seasons:
        cards = []
        for e in s["episodes"]:
            lp = e["palette"]["light"]
            dp = e["palette"]["dark"]
            style = (f"--l-bg:{lp['paper']};--l-fg:{lp['fg']};--l-accent:{lp['accent']};"
                     f"--d-bg:{dp['paper']};--d-fg:{dp['fg']};--d-accent:{dp['accent']};"
                     f"--ep-display:'{e['fonts']['display']}',Impact,sans-serif")
            cards.append(f'<a class="ep" style="{style}" href="{s["dir"]}/{e["dir"]}/index.html">'
                         f'<span class="k">Episode {e["number"]} · {len(e["chapters"])} chapters</span>'
                         f'<span class="t">{html.escape(e["title"])}</span>'
                         f'<span class="s">{html.escape(e["summary"])}</span></a>')
        blocks.append(f"""<section class="season">
<p class="eyebrow"><b>Season {s['number']}</b></p>
<h2>{html.escape(s['title'])}</h2>
<p class="mood">{html.escape(s['summary'])}</p>
<div class="eps">{''.join(cards)}</div>
<p class="soon">More episodes are being written.</p>
</section>""")
    first = seasons[0]["episodes"][0]
    start = f"{seasons[0]['dir']}/{first['dir']}/{first['chapters'][0]['slug']}.html"
    body = f"""
<main class="wrap wide">
<section class="cover">
<p class="eyebrow"><b>A serial</b> · by {html.escape(series['author'])}</p>
<h1>{html.escape(series['title'])}</h1>
<p class="lede">{html.escape(series['logline'])}</p>
<p><a class="eyebrow" href="{start}"><b>Start reading →</b></a></p>
</section>
{''.join(blocks)}
</main>
{footer(series)}"""
    return page(series["title"], SERIES_THEME, body, series["logline"], depth=0)


def build():
    series, seasons = load_story()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    (OUT / ".nojekyll").write_text("")
    (OUT / "base.css").write_text(BASE_CSS.strip() + "\n", encoding="utf-8")
    flat = [(s, e, c) for s in seasons for e in s["episodes"] for c in e["chapters"]]
    pos = 0
    for s in seasons:
        for e in s["episodes"]:
            d = OUT / s["dir"] / e["dir"]
            d.mkdir(parents=True)
            (d / "index.html").write_text(build_episode(series, s, e), encoding="utf-8")
            for i, c in enumerate(e["chapters"]):
                (d / f"{c['slug']}.html").write_text(build_chapter(series, s, e, i, flat, pos), encoding="utf-8")
                pos += 1
    (OUT / "index.html").write_text(build_index(series, seasons), encoding="utf-8")
    total = sum(c["words"] for _, _, c in flat)
    print(f"Built {len(flat)} chapters ({total:,} words) into {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    build()
