#!/usr/bin/env python3
"""Render the repository's markdown into one self-contained preview.html.

Offline, no dependencies: a small purpose-built markdown converter that covers exactly what these
docs use (headings, pipe tables, fenced code, lists, quotes, images, links, inline code/bold/italic).

  python tools/make_preview.py          -> writes ../preview.html

Edit the .md files, re-run this, hit reload in the browser.
"""
import os, re, html, glob

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", t)
    # images
    t = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)",
               r'<img alt="\1" src="\2" loading="lazy">', t)
    # links: other docs become in-page doc switches, anchors are dropped for local files
    def link(m):
        label, href = m.group(1), m.group(2)
        # keys must match the article ids exactly: docs/NN-*.md, patches/README.md, tools/README.md
        mm = re.match(r"^(?:\.\./)?(?:docs/|patches/|tools/)?(\d\d-[a-z0-9-]+\.md)(?:#.*)?$", href)
        if mm:
            return f'<a href="#doc:docs/{mm.group(1)}" class="doclink">{label}</a>'
        mm = re.match(r"^(?:\.\./)?(patches|tools)/(README\.md)(?:#.*)?$", href)
        if mm:
            return f'<a href="#doc:{mm.group(1)}/{mm.group(2)}" class="doclink">{label}</a>'
        if href.startswith("#"):
            return f'<span class="anchorlink">{label}</span>'
        return f'<a href="{href}" target="_blank" rel="noopener">{label}</a>'
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, t)
    return t

def md_to_html(md):
    out, i, lines = [], 0, md.split("\n")
    n = len(lines)
    while i < n:
        ln = lines[i]
        # fenced code
        if ln.strip().startswith("```"):
            lang = ln.strip()[3:].strip()
            buf = []; i += 1
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            body = html.escape("\n".join(buf))
            out.append(f'<pre class="code{" "+lang if lang else ""}"><code>{body}</code></pre>')
            continue
        # table
        if ln.strip().startswith("|") and i + 1 < n and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i+1]):
            head = [c.strip() for c in ln.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            t = ["<table><thead><tr>"]
            t += [f"<th>{inline(c)}</th>" for c in head]
            t.append("</tr></thead><tbody>")
            for r in rows:
                r += [""] * (len(head) - len(r))
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r[:len(head)]) + "</tr>")
            t.append("</tbody></table>")
            out.append("".join(t))
            continue
        # headings
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            lvl = len(m.group(1)); txt = inline(m.group(2))
            slug = re.sub(r"[^a-z0-9]+", "-", m.group(2).lower()).strip("-")
            out.append(f'<h{lvl} id="{slug}">{txt}</h{lvl}>')
            i += 1
            continue
        # hr
        if re.match(r"^\s*(---|\*\*\*)\s*$", ln):
            out.append("<hr>"); i += 1; continue
        # blockquote
        if ln.strip().startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip()); i += 1
            out.append("<blockquote>" + inline(" ".join(buf)) + "</blockquote>")
            continue
        # lists
        if re.match(r"^\s*([-*]|\d+\.)\s+", ln):
            ordered = bool(re.match(r"^\s*\d+\.\s+", ln))
            items = []
            while i < n and re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]):
                items.append(re.sub(r"^\s*([-*]|\d+\.)\s+", "", lines[i]))
                i += 1
                while i < n and lines[i].startswith("   ") and lines[i].strip():
                    items[-1] += " " + lines[i].strip(); i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
            continue
        # blanks
        if not ln.strip():
            i += 1; continue
        # paragraph
        buf = []
        while i < n and lines[i].strip() and not re.match(r"^(#{1,6}\s|```|\s*\|)", lines[i]) \
                and not re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]) and not lines[i].strip().startswith(">"):
            buf.append(lines[i].strip()); i += 1
        out.append("<p>" + inline(" ".join(buf)) + "</p>")
    return "\n".join(out)

def main():
    docs = [("README.md", "Read me first")]
    for p in sorted(glob.glob(os.path.join(ROOT, "docs", "*.md"))):
        rel = "docs/" + os.path.basename(p)
        docs.append((rel, os.path.basename(p)))
    for p in ("patches/README.md", "tools/README.md"):
        if os.path.exists(os.path.join(ROOT, p)):
            docs.append((p, p))
    sections, nav = [], []
    for rel, label in docs:
        src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        # docs live one level down; the preview sits at the root where the images are
        src = src.replace("](../", "](")
        body = md_to_html(src)
        key = rel.replace("/", "-")
        hidden = "" if rel == "README.md" else " hidden"
        sections.append(f'<article id="doc:{rel}" data-key="{rel}"{hidden}>{body}'
                        f'<p class="src">source: <code>{rel}</code></p></article>')
        nav.append(f'<a href="#doc:{rel}" data-doc="{rel}">{html.escape(label)}</a>')
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>kenwood-dnn990hd — preview</title>
<style>
:root {{ color-scheme: light dark; }}
body {{ margin:0; font:16px/1.6 -apple-system,"Segoe UI",Roboto,sans-serif;
        background:#f6f7f9; color:#1c2024; }}
header {{ position:sticky; top:0; z-index:9; background:#fff; border-bottom:1px solid #d8dde3;
          padding:10px 20px; display:flex; gap:14px; align-items:baseline; flex-wrap:wrap; }}
header b {{ font-size:15px; }}
header span {{ font-size:13px; color:#66707a; }}
#wrap {{ display:flex; align-items:flex-start; }}
nav {{ position:sticky; top:56px; width:250px; padding:18px 14px; font-size:14px;
       border-right:1px solid #e2e6ea; height:calc(100vh - 56px); overflow:auto; background:#fbfcfd; }}
nav a {{ display:block; padding:6px 9px; border-radius:6px; color:#2a323b; text-decoration:none; }}
nav a:hover {{ background:#eef2f6; }}
nav a.on {{ background:#dbe8f7; font-weight:600; }}
main {{ flex:1; min-width:0; padding:26px 40px 80px; max-width:1000px; }}
h1,h2,h3,h4 {{ line-height:1.25; margin:1.5em 0 .55em; }}
h1 {{ font-size:29px; border-bottom:2px solid #e4e8ec; padding-bottom:.3em; margin-top:0; }}
h2 {{ font-size:22px; border-bottom:1px solid #e9edf1; padding-bottom:.25em; }}
h3 {{ font-size:18px; }}
p,li,td,th {{ }}
code {{ background:#eceff3; padding:.12em .35em; border-radius:4px; font-size:.9em;
        font-family:Consolas,"Cascadia Mono",monospace; }}
pre.code {{ background:#1e2329; color:#e6edf3; padding:14px 16px; border-radius:8px;
            overflow:auto; font-size:13.5px; line-height:1.5; }}
pre.code code {{ background:none; padding:0; color:inherit; }}
table {{ border-collapse:collapse; margin:1em 0; width:100%; font-size:14.5px; display:block; overflow:auto; }}
th,td {{ border:1px solid #dfe4e9; padding:7px 11px; text-align:left; vertical-align:top; }}
th {{ background:#f0f3f6; }}
tr:nth-child(even) td {{ background:#fafbfc; }}
img {{ max-width:100%; height:auto; border:1px solid #d8dde3; border-radius:8px; margin:10px 0; background:#fff; }}
blockquote {{ margin:1em 0; padding:.6em 1em; border-left:4px solid #c8a03a; background:#fdf8e8; }}
.anchorlink {{ border-bottom:1px dotted #889; }}
.src {{ margin-top:2.5em; font-size:12.5px; color:#7b858f; border-top:1px dashed #dde2e8; padding-top:.7em; }}
@media (prefers-color-scheme: dark) {{
 body {{ background:#12161a; color:#e6edf3; }}
 header,nav {{ background:#171c21; border-color:#2a323b; }}
 nav a {{ color:#cfd8e1; }} nav a:hover {{ background:#1f262d; }} nav a.on {{ background:#243244; }}
 h1,h2 {{ border-color:#2a323b; }}
 code {{ background:#1e252c; }}
 th {{ background:#1c232a; }} td,th {{ border-color:#2a323b; }}
 tr:nth-child(even) td {{ background:#171d23; }}
 img {{ background:#0b0e11; border-color:#2a323b; }}
 blockquote {{ background:#241f10; border-left-color:#c8a03a; }}
}}
</style></head><body>
<header><b>kenwood-dnn990hd</b>
<span>local preview — generated by <code>tools/make_preview.py</code>; edit the .md files and re-run it</span></header>
<div id="wrap">
<nav>{''.join(nav)}</nav>
<main>{''.join(sections)}</main>
</div>
<script>
function show(k){{
  document.querySelectorAll('article').forEach(function(a){{
    a.hidden = a.dataset.key !== k;
  }});
  document.querySelectorAll('nav a').forEach(function(a){{
    a.classList.toggle('on', a.dataset.doc === k);
  }});
}}
document.addEventListener('click', function(e){{
  var a = e.target.closest('a.doclink, nav a');
  if(!a) return;
  var k = a.dataset.doc || a.getAttribute('href').slice(5);
  if (k) {{ e.preventDefault(); show(k); window.scrollTo(0,0); location.hash = 'doc:'+k; }}
}});
var h = decodeURIComponent(location.hash || '').slice(5);
show(document.getElementById('doc:'+h) ? h : 'README.md');
</script></body></html>"""
    out = os.path.join(ROOT, "preview.html")
    open(out, "w", encoding="utf-8").write(page)
    print(f"wrote {out}  ({len(page):,} bytes, {len(docs)} documents)")

if __name__ == "__main__":
    main()
