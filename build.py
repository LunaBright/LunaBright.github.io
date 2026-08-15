#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py - LunaBright 个人主页静态站点生成器（Python 3.8+，仅标准库）

功能：
  1. 读取 data/site.json 作为站点设置（名称、头像、背景图、评论区等）
  2. 把 posts/*.md 渲染为 blog/posts/*.html（支持表格、LaTeX 公式、图片扩展语法、草稿）
  3. 更新 blog/index.html 博客列表（分类 / 标签过滤 + 全文搜索）
  4. 更新 index.html 首页（最新文章、关于我、技能、联系方式）
  5. 生成 feed.xml Atom 订阅与 search 索引

用法：
  python build.py               # 输出到仓库根目录（本地预览）
  python build.py --out _site   # 输出到 _site（GitHub Actions 部署）
"""

import argparse
import html as html_mod
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parent

# ============ 默认站点设置（data/site.json 会覆盖） ============
DEFAULT_SITE = {
    "site_name": "LunaBright",
    "site_url": "https://lunabright.github.io",
    "description": "LunaBright 的个人主页：技术笔记、学习心得与生活记录",
    "author": "LunaBright",
    "email": "2154626568@qq.com",
    "github": "https://github.com/LunaBright",
    "avatar": "/assets/images/avatar.svg",
    "background": "/assets/images/background.svg",
    "tagline": "程序员 · 学习者 · 生活记录者",
    "hero_desc": "这里是我在互联网上的一个小家，用来展示自己、沉淀知识、记录生活。欢迎常来逛逛。",
    "about": [],
    "skills": [],
    "contact": [],
    "home_recent": 3,
    "giscus": {"repo": "", "repo_id": "", "category": "", "category_id": ""},
}

POSTS_DIR = ROOT / "posts"
PAGES_DIR = ROOT / "pages"
TEMPLATES_DIR = ROOT / "templates"
DATA_DIR = ROOT / "data"

OUT = ROOT  # 默认输出到仓库根目录，--out 可覆盖

# ============ 基础工具 ============


def log(msg):
    print(msg)


def write_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    log("  生成 %s" % path.relative_to(OUT).as_posix())


def copy_tree(src, dst):
    if src.exists():
        if dst.resolve() == src.resolve():
            return
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)


def render_template(name, tokens):
    text = (TEMPLATES_DIR / name).read_text(encoding="utf-8")
    for key, value in tokens.items():
        text = text.replace("{{%s}}" % key, value)
    return text


def render_page(name, tokens):
    text = (PAGES_DIR / name).read_text(encoding="utf-8")
    for key, value in tokens.items():
        text = text.replace("{{%s}}" % key, value)
    return text


def date_display(date_str):
    """2026-08-08 -> 2026 年 8 月 8 日"""
    date_str = str(date_str)[:10]
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return "%d 年 %d 月 %d 日" % (dt.year, dt.month, dt.day)
    except ValueError:
        return date_str


def load_site():
    site = dict(DEFAULT_SITE)
    path = DATA_DIR / "site.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            site.update(data)
        except Exception as exc:
            print("警告：data/site.json 解析失败，使用默认配置：%s" % exc)
    for key in ("about", "skills", "contact"):
        if not isinstance(site.get(key), list):
            site[key] = []
    giscus = site.get("giscus") or {}
    site["giscus"] = dict(DEFAULT_SITE["giscus"], **giscus)
    return site


def attr_escape(value):
    return html_mod.escape(value, quote=True)


# ============ 极简 Markdown 解析 ============

MATH_RE = re.compile(r"(\$\$[^$\n]+\$\$|\$[^$\n]+\$)")
CODE_RE = re.compile(r"`([^`\n]+)`")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)")
IMAGE_RE = re.compile(
    r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"((?:[^\"]|\\\")*)\")?\)"
)
BOLD_RE = re.compile(r"\*\*([^*\n]+)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
STRIKE_RE = re.compile(r"~~([^~\n]+)~~")


def safe_url(url):
    url = url.strip()
    if url.lower().startswith(("javascript:", "vbscript:", "data:")):
        return "#"
    return url


def safe_img_url(url):
    """图片 src 比普通链接宽松：允许 data:image 内嵌图（后台粘贴图片失败时的兜底）。"""
    url = url.strip()
    low = url.lower()
    if low.startswith("data:image/") and ";" in low and "," in low:
        return url
    return safe_url(url)


def protect_math(text):
    """把 $...$ / $$...$$ 先替换成占位符，避免被粗体/斜体规则破坏，最后还原。"""
    tokens = []

    def rep(m):
        tokens.append(m.group(0))
        return "\x00M%d\x00" % (len(tokens) - 1)

    return MATH_RE.sub(rep, text), tokens


def restore_math(text, tokens):
    for idx, tok in enumerate(tokens):
        text = text.replace("\x00M%d\x00" % idx, tok)
    return text


def parse_img_options(title):
    """解析图片扩展语法：![说明](地址 "width:60%,align:center,figcaption:图注")"""
    opts = {}
    if not title:
        return opts
    for part in title.split(","):
        part = part.strip()
        if ":" in part:
            key, value = part.split(":", 1)
            opts[key.strip().lower()] = value.strip()
    return opts


def img_html(m):
    alt = m.group(1)
    src = safe_img_url(m.group(2))
    opts = parse_img_options(m.group(3) or "")
    width = opts.get("width")
    align = opts.get("align", "center" if opts else "")
    caption = opts.get("figcaption") or opts.get("caption")
    style = ' style="width:%s"' % html_mod.escape(width) if width else ""
    img = '<img src="%s" alt="%s" loading="lazy"%s>' % (src, alt, style)
    if opts:
        cls = "align-%s" % align if align in ("left", "center", "right") else "align-center"
        if caption:
            return '<figure class="%s">%s<figcaption>%s</figcaption></figure>' % (
                cls,
                img,
                html_mod.escape(caption),
            )
        return '<figure class="%s">%s</figure>' % (cls, img)
    return img


def md_inline(text):
    """行内语法：公式、代码、图片、链接、粗体、斜体、删除线。"""
    text = html_mod.escape(text, quote=False)
    text, math_tokens = protect_math(text)

    text = CODE_RE.sub(lambda m: "<code>%s</code>" % m.group(1), text)
    text = IMAGE_RE.sub(img_html, text)
    text = LINK_RE.sub(
        lambda m: '<a href="%s" title="%s">%s</a>'
        % (safe_url(m.group(2)), html_mod.escape(m.group(3) or ""), m.group(1)),
        text,
    )
    text = BOLD_RE.sub(r"<strong>\1</strong>", text)
    text = ITALIC_RE.sub(r"<em>\1</em>", text)
    text = STRIKE_RE.sub(r"<del>\1</del>", text)
    return restore_math(text, math_tokens)


def split_table_row(line):
    line = line.strip()
    line = line.replace("\\|", "\x00P\x00")
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.replace("\x00P\x00", "|").strip() for cell in line.split("|")]


def table_align(cell):
    cell = cell.strip()
    left = cell.startswith(":")
    right = cell.endswith(":")
    if left and right:
        return ' style="text-align:center"'
    if right:
        return ' style="text-align:right"'
    if left:
        return ' style="text-align:left"'
    return ""


def render_table(rows):
    if len(rows) < 2:
        return "<p>%s</p>" % md_inline(" ".join(rows))
    header = split_table_row(rows[0])
    aligns = [table_align(c) for c in split_table_row(rows[1])]
    body_rows = [split_table_row(r) for r in rows[2:]]
    thead = "<thead><tr>" + "".join(
        "<th%s>%s</th>" % (aligns[i] if i < len(aligns) else "", md_inline(c))
        for i, c in enumerate(header)
    ) + "</tr></thead>"
    tbody = "<tbody>" + "".join(
        "<tr>"
        + "".join(
            "<td%s>%s</td>" % (aligns[i] if i < len(aligns) else "", md_inline(c))
            for i, c in enumerate(row)
        )
        + "</tr>"
        for row in body_rows
    ) + "</tbody>"
    return '<div class="table-wrap"><table>%s%s</table></div>' % (thead, tbody)


def md_to_html(md):
    """块级 Markdown 解析：标题、代码块、表格、公式、引用、列表、图片、段落。"""
    lines = md.split("\n")
    blocks = []
    i, n = 0, len(lines)

    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        # 围栏代码块
        if re.match(r"^\s*```", line):
            lang = line.strip()[3:].strip()
            buf = []
            i += 1
            while i < n and not re.match(r"^\s*```\s*$", lines[i]):
                buf.append(lines[i])
                i += 1
            i += 1
            blocks.append(("code", (lang, "\n".join(buf))))
            continue

        # 标题
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            blocks.append(("h%d" % level, md_inline(m.group(2).strip())))
            i += 1
            continue

        # 分割线
        if re.match(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$", line):
            blocks.append(("hr", ""))
            i += 1
            continue

        # 块级公式
        if line.strip().startswith("$$"):
            buf = [line.strip()]
            i += 1
            if not (len(buf[0]) > 2 and buf[0].endswith("$$")):
                while i < n and not lines[i].strip().endswith("$$"):
                    buf.append(lines[i].rstrip())
                    i += 1
                if i < n:
                    buf.append(lines[i].strip())
                    i += 1
            blocks.append(("math", "\n".join(buf)))
            continue

        # 表格
        if line.lstrip().startswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            blocks.append(("table", rows))
            continue

        # 引用
        if line.lstrip().startswith(">"):
            buf = []
            while i < n and lines[i].lstrip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            blocks.append(("quote", md_to_html("\n".join(buf))))
            continue

        # 列表
        if re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", line):
            ordered = bool(re.match(r"^\s*\d+[.)]", line))
            items = []
            while i < n and lines[i].strip():
                m = re.match(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$", lines[i])
                if not m:
                    break
                items.append(md_inline(m.group(1).strip()))
                i += 1
            blocks.append(("list", (ordered, items)))
            continue

        # 独立图片行 -> 块级 figure
        if re.match(r"^\s*!\[[^\]]*\]\([^)]*\)\s*$", line):
            blocks.append(("figure", md_inline(line.strip())))
            i += 1
            continue

        # 段落
        buf = []
        block_start = re.compile(
            r"^\s*(?:```|#{1,6}\s|>|[-*+]\s+|\d+[.)]\s+|-{3,}\s*$|\*{3,}\s*$|\$\$|\|)"
        )
        while i < n and lines[i].strip():
            if buf and block_start.match(lines[i]):
                break
            buf.append(lines[i].strip())
            i += 1
        blocks.append(("p", md_inline(" ".join(buf))))

    out = []
    for typ, content in blocks:
        if typ == "code":
            lang, code = content
            cls = ' class="lang-%s"' % html_mod.escape(lang) if lang else ""
            out.append("<pre><code%s>%s</code></pre>" % (cls, html_mod.escape(code)))
        elif typ == "hr":
            out.append("<hr>")
        elif typ.startswith("h"):
            level = int(typ[1:])
            out.append("<h%d>%s</h%d>" % (level, content, level))
        elif typ == "quote":
            out.append("<blockquote>%s</blockquote>" % content)
        elif typ == "list":
            ordered, items = content
            tag = "ol" if ordered else "ul"
            lis = "".join("<li>%s</li>" % item for item in items)
            out.append("<%s>%s</%s>" % (tag, lis, tag))
        elif typ == "table":
            out.append(render_table(content))
        elif typ == "math":
            out.append('<div class="prose-math">%s</div>' % html_mod.escape(content))
        elif typ == "figure":
            out.append(content)
        elif typ == "p":
            out.append("<p>%s</p>" % content)
    return "\n".join(out)


# ============ 文章读取（front matter 解析） ============

FRONT_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.S)


def parse_scalar(val):
    val = val.strip()
    if len(val) >= 2 and val[0] in "\"'" and val[-1] == val[0]:
        return val[1:-1]
    if val.lower() == "true":
        return True
    if val.lower() == "false":
        return False
    if val.lower() in ("null", "~"):
        return None
    if val.startswith("[") and val.endswith("]"):
        return [
            parse_scalar(x)
            for x in val[1:-1].split(",")
            if x.strip()
        ]
    return val


def parse_front_matter(text):
    """解析 front matter（YAML 子集）：标题 / 日期 / 分类 / 标签 / 摘要 / 草稿 / 封面。"""
    meta = {}
    body = text
    m = FRONT_RE.match(text)
    if not m:
        return meta, body.strip()
    body = text[m.end():]
    lines = m.group(1).splitlines()
    i, n = 0, len(lines)
    while i < n:
        line = lines[i].rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        km = re.match(r"^([A-Za-z_][\w]*)\s*:\s*(.*)$", line)
        if not km:
            i += 1
            continue
        key = km.group(1).lower()
        val = km.group(2).strip()
        if val in ("", "|", ">"):
            block = []
            i += 1
            if i < n and re.match(r"^\s*-\s+", lines[i]):
                while i < n:
                    lm = re.match(r"^\s*-\s+(.*)$", lines[i])
                    if not lm:
                        break
                    block.append(parse_scalar(lm.group(1)))
                    i += 1
                meta[key] = block
            else:
                while i < n and lines[i].strip() and not re.match(
                    r"^[A-Za-z_][\w]*\s*:", lines[i]
                ):
                    block.append(lines[i].strip())
                    i += 1
                meta[key] = " ".join(block)
            continue
        meta[key] = parse_scalar(val)
        i += 1
    return meta, body.strip()


def read_posts():
    posts = []
    if not POSTS_DIR.exists():
        return posts
    for md_file in sorted(POSTS_DIR.glob("*.md")):
        meta, body = parse_front_matter(md_file.read_text(encoding="utf-8"))
        if meta.get("draft") is True:
            log("  跳过草稿：%s" % md_file.name)
            continue
        slug = md_file.stem
        title = str(meta.get("title") or slug)
        date = str(meta.get("date") or slug[:10])
        category = str(meta.get("category") or "随笔").strip()
        raw_tags = meta.get("tags") or []
        tags = [str(t).strip() for t in raw_tags if str(t).strip()]
        content_html = md_to_html(body)
        plain = re.sub(r"<[^>]+>", " ", content_html)
        plain = re.sub(r"\s+", " ", plain).strip()
        excerpt = str(meta.get("excerpt") or plain[:120].rstrip())
        minutes = max(1, round(len(plain) / 500))
        cover = str(meta.get("cover") or "").strip()
        posts.append(
            {
                "slug": slug,
                "title": title,
                "date": date,
                "date_display": date_display(date),
                "category": category,
                "tags": tags,
                "cover": cover,
                "excerpt": excerpt,
                "content_html": content_html,
                "plain": plain,
                "minutes": minutes,
            }
        )
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


# ============ 组件生成 ============


def tags_html(tags):
    return "".join('<span class="tag">%s</span>' % html_mod.escape(t) for t in tags)


def cover_html(post, base):
    if not post.get("cover"):
        return ""
    return (
        '<div class="post-cover"><img src="%s" alt="%s 封面" loading="lazy"></div>'
        % (safe_img_url(post["cover"]), html_mod.escape(post["title"]))
    )


def post_card(post, base):
    cover = cover_html(post, base)
    return (
        '<article class="post-card reveal" data-category="%s" data-tags="%s" data-title="%s">\n'
        '  <a class="post-card-link" href="%sblog/posts/%s.html">\n'
        "    %s\n"
        '    <div class="post-card-meta"><time datetime="%s">%s</time><span>·</span><span class="post-card-category">%s</span></div>\n'
        '    <h3 class="post-card-title">%s</h3>\n'
        '    <p class="post-card-excerpt">%s</p>\n'
        '    <div class="post-card-tags">%s</div>\n'
        "  </a>\n"
        "</article>"
    ) % (
        attr_escape(post["category"]),
        attr_escape(",".join(post["tags"])),
        attr_escape(post["title"]),
        base,
        post["slug"],
        cover,
        post["date"],
        post["date"],
        html_mod.escape(post["category"]),
        html_mod.escape(post["title"]),
        html_mod.escape(post["excerpt"]),
        tags_html(post["tags"]),
    )


def post_row(post, base):
    return (
        '<article class="post-list-item reveal" data-category="%s" data-tags="%s" data-title="%s" data-excerpt="%s">\n'
        '  <time class="post-list-date" datetime="%s">%s</time>\n'
        '  <div class="post-list-main">\n'
        '    <h2 class="post-list-title"><a href="%sblog/posts/%s.html">%s</a></h2>\n'
        '    <p class="post-list-meta"><span class="post-list-category">%s</span><span>·</span><span>约 %d 分钟</span></p>\n'
        '    <p class="post-list-excerpt">%s</p>\n'
        '    <div class="post-list-tags">%s</div>\n'
        "  </div>\n"
        "</article>"
    ) % (
        attr_escape(post["category"]),
        attr_escape(",".join(post["tags"])),
        attr_escape(post["title"]),
        attr_escape(post["excerpt"]),
        post["date"],
        post["date"],
        base,
        post["slug"],
        html_mod.escape(post["title"]),
        html_mod.escape(post["category"]),
        post["minutes"],
        html_mod.escape(post["excerpt"]),
        tags_html(post["tags"]),
    )


def page_shell(title, desc, base, body, site, home_active="", blog_active="", extra_head=""):
    header = render_template(
        "header.html",
        {
            "TITLE": title,
            "DESC": desc,
            "BASE": base,
            "HOME_ACTIVE": home_active,
            "BLOG_ACTIVE": blog_active,
            "SITE_NAME": html_mod.escape(site["site_name"]),
            "GITHUB_URL": site["github"],
            "CMS_URL": "https://app.pagescms.org/" + site["giscus"]["repo"],
            "BACKGROUND": site["background"],
            "EXTRA_HEAD": extra_head,
        },
    )
    footer = render_template(
        "footer.html",
        {"BASE": base, "SITE_NAME": html_mod.escape(site["site_name"]), "GITHUB_URL": site["github"]},
    )
    return header + body + footer


def categories_of(posts):
    seen = []
    for p in posts:
        if p["category"] not in seen:
            seen.append(p["category"])
    return seen


def tags_of(posts):
    seen = []
    for p in posts:
        for t in p["tags"]:
            if t not in seen:
                seen.append(t)
    return seen


def filter_chips(values, kind):
    items = ['<button class="filter-chip active" type="button" data-filter="%s" data-value="">全部</button>' % kind]
    for v in values:
        items.append(
            '<button class="filter-chip" type="button" data-filter="%s" data-value="%s">%s</button>'
            % (kind, attr_escape(v), html_mod.escape(v))
        )
    return "\n".join(items)


# ============ 页面构建 ============


def build_home(posts, site):
    log("构建首页 index.html")
    recent = posts[: int(site.get("home_recent") or 3)]
    cards = "\n".join(post_card(p, "") for p in recent)
    about = "\n".join('<p class="reveal">%s</p>' % para for para in site.get("about") or [])
    skills = "\n".join(
        '<span class="chip reveal">%s</span>' % html_mod.escape(s)
        for s in site.get("skills") or []
    )
    contacts = "\n".join(
        '<a class="contact-card reveal" href="%s" target="_blank" rel="noopener">%s %s</a>'
        % (safe_url(c["url"]), html_mod.escape(c.get("label", "")), html_mod.escape(c.get("value", "")))
        for c in site.get("contact") or []
    )
    tokens = {
        "BASE": "",
        "AVATAR": site["avatar"],
        "AUTHOR": html_mod.escape(site["author"]),
        "EMAIL": html_mod.escape(site["email"]),
        "GITHUB": "@" + html_mod.escape(site["github"].rstrip("/").rsplit("/", 1)[-1]),
        "TAGLINE": html_mod.escape(site.get("tagline") or ""),
        "HERO_DESC": html_mod.escape(site.get("hero_desc") or ""),
        "ABOUT_PARAGRAPHS": about,
        "SKILL_CHIPS": skills,
        "CONTACT_CARDS": contacts,
    }
    body = render_page("home.html", tokens).replace("<!-- RECENT_POSTS -->", cards)
    title = "%s · %s" % (site["site_name"], site["description"])
    write_text(
        OUT / "index.html",
        page_shell(title, site["description"], "", body, site, home_active=" active"),
    )


def build_blog_index(posts, site):
    log("构建博客列表 blog/index.html")
    rows = "\n".join(post_row(p, "../") for p in posts)
    index = [
        {
            "title": p["title"],
            "url": "posts/%s.html" % p["slug"],
            "date": p["date"],
            "category": p["category"],
            "tags": p["tags"],
            "excerpt": p["excerpt"],
            "content": p["plain"][:4000],
        }
        for p in posts
    ]
    index_json = json.dumps(index, ensure_ascii=False).replace("<", "\\u003c")
    tokens = {
        "BASE": "../",
        "CATEGORY_CHIPS": filter_chips(categories_of(posts), "category"),
        "TAG_CHIPS": filter_chips(tags_of(posts), "tag"),
        "SEARCH_INDEX": index_json,
    }
    body = (
        render_page("blog.html", tokens)
        .replace("<!-- POST_LIST -->", rows)
        .replace("<!-- SEARCH_INDEX -->", index_json)
    )
    write_text(
        OUT / "blog" / "index.html",
        page_shell("博客 · " + site["site_name"], site["description"] + "：博客文章列表", "../", body, site, blog_active=" active"),
    )


def build_post_pages(posts, site):
    log("构建文章页面 blog/posts/")
    katex = (
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">\n'
        '  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>\n'
        '  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>'
    )
    for idx, post in enumerate(posts):
        prev = posts[idx + 1] if idx + 1 < len(posts) else None
        nxt = posts[idx - 1] if idx > 0 else None
        pager = ""
        if prev or nxt:
            parts = []
            if prev:
                parts.append(
                    '<a class="pager-prev" href="%s.html"><span class="pager-label">← 上一篇</span>%s</a>'
                    % (prev["slug"], html_mod.escape(prev["title"]))
                )
            else:
                parts.append("<span></span>")
            if nxt:
                parts.append(
                    '<a class="pager-next" href="%s.html"><span class="pager-label">下一篇 →</span>%s</a>'
                    % (nxt["slug"], html_mod.escape(nxt["title"]))
                )
            else:
                parts.append("<span></span>")
            pager = '<nav class="post-pager" aria-label="上一篇 / 下一篇">%s</nav>' % "".join(parts)

        giscus = site.get("giscus") or {}
        if giscus.get("repo_id") and giscus.get("category_id"):
            comments = (
                '<section class="comments" id="comments">\n'
                '  <div class="container container-narrow">\n'
                '    <h2 class="comments-title">评论</h2>\n'
                '    <script src="https://giscus.app/client.js"\n'
                '      data-repo="%s"\n'
                '      data-repo-id="%s"\n'
                '      data-category="%s"\n'
                '      data-category-id="%s"\n'
                '      data-mapping="pathname"\n'
                '      data-strict="0"\n'
                '      data-reactions-enabled="1"\n'
                '      data-emit-metadata="0"\n'
                '      data-input-position="bottom"\n'
                '      data-theme="preferred_color_scheme"\n'
                '      data-lang="zh-CN"\n'
                '      crossorigin="anonymous"\n'
                "      async>\n"
                "    </script>\n"
                "  </div>\n"
                "</section>"
            ) % (
                attr_escape(giscus["repo"]),
                attr_escape(giscus["repo_id"]),
                attr_escape(giscus["category"]),
                attr_escape(giscus["category_id"]),
            )
        else:
            comments = (
                '<section class="comments" id="comments">\n'
                '  <div class="container container-narrow">\n'
                '    <h2 class="comments-title">评论</h2>\n'
                '    <p class="comments-placeholder">评论区尚未启用：在 <code>data/site.json</code> 的 giscus 配置里填好 repo_id 与 category_id 即可开启（详见 README）。</p>\n'
                "  </div>\n"
                "</section>"
            )

        body = (
            '<article class="post">\n'
            '  <div class="container container-narrow">\n'
            "    %s\n"
            '    <header class="post-header">\n'
            '      <p class="page-eyebrow"><a href="../index.html">← 返回博客</a></p>\n'
            '      <h1 class="post-title">%s</h1>\n'
            '      <div class="post-meta">\n'
            '        <span class="post-category">%s</span>\n'
            '        <time datetime="%s">%s</time>\n'
            '        <span>·</span>\n'
            '        <span>约 %d 分钟阅读</span>\n'
            "        %s\n"
            "      </div>\n"
            "    </header>\n"
            '    <div class="prose">\n%s\n    </div>\n'
            "    %s\n"
            "  </div>\n"
            "</article>"
            + comments
        ) % (
            cover_html(post, "../../"),
            html_mod.escape(post["title"]),
            html_mod.escape(post["category"]),
            post["date"],
            post["date_display"],
            post["minutes"],
            tags_html(post["tags"]),
            post["content_html"],
            pager,
        )
        write_text(
            OUT / "blog" / "posts" / (post["slug"] + ".html"),
            page_shell(
                post["title"] + " · " + site["site_name"],
                post["excerpt"],
                "../../",
                body,
                site,
                blog_active=" active",
                extra_head=katex,
            ),
        )


def build_404(site):
    log("构建 404 页面")
    body = render_page("404.html", {"BASE": "./"})
    write_text(
        OUT / "404.html",
        page_shell("页面走丢了 · " + site["site_name"], "404 页面", "./", body, site),
    )


def build_feed(posts, site):
    log("生成 Atom 订阅 feed.xml")
    entries = []
    for p in posts:
        url = "%s/blog/posts/%s.html" % (site["site_url"], p["slug"])
        entries.append(
            "  <entry>\n"
            "    <title>%s</title>\n"
            '    <link href="%s"/>\n'
            '    <id>%s</id>\n'
            "    <updated>%sT00:00:00+08:00</updated>\n"
            "    <category term=\"%s\"/>\n"
            "    <author><name>%s</name></author>\n"
            "    <summary>%s</summary>\n"
            '    <content type="html">%s</content>\n'
            "  </entry>" % (
                xml_escape(p["title"]),
                xml_escape(url),
                xml_escape(url),
                p["date"],
                xml_escape(p["category"]),
                xml_escape(site["author"]),
                xml_escape(p["excerpt"]),
                xml_escape(p["content_html"]),
            )
        )
    feed = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<feed xmlns="http://www.w3.org/2005/Atom">\n'
        "  <title>%s</title>\n"
        "  <subtitle>%s</subtitle>\n"
        '  <link href="%s/feed.xml" rel="self"/>\n'
        '  <link href="%s/" rel="alternate"/>\n'
        "  <updated>%sT00:00:00+08:00</updated>\n"
        "  <author><name>%s</name><email>%s</email></author>\n"
        "  <id>%s</id>\n"
        "%s\n"
        "</feed>\n"
    ) % (
        xml_escape(site["site_name"]),
        xml_escape(site["description"]),
        site["site_url"],
        site["site_url"],
        posts[0]["date"] if posts else datetime.now().strftime("%Y-%m-%d"),
        xml_escape(site["author"]),
        xml_escape(site["email"]),
        site["site_url"] + "/",
        "\n".join(entries),
    )
    write_text(OUT / "feed.xml", feed)


def copy_static():
    log("复制静态资源")
    copy_tree(ROOT / "assets", OUT / "assets")
    if (ROOT / "media").exists():
        copy_tree(ROOT / "media", OUT / "media")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="LunaBright 站点生成器")
    parser.add_argument("--out", default=str(ROOT), help="输出目录（默认仓库根目录）")
    args = parser.parse_args()
    global OUT
    OUT = Path(args.out).resolve()

    print("=" * 52)
    print("  LunaBright 站点生成器")
    print("=" * 52)
    site = load_site()
    posts = read_posts()
    print("共读取 %d 篇文章" % len(posts))
    build_home(posts, site)
    build_blog_index(posts, site)
    build_post_pages(posts, site)
    build_404(site)
    build_feed(posts, site)
    copy_static()
    print("\n完成！输出目录：%s" % OUT)
    if OUT == ROOT:
        print("本地预览：python -m http.server 8000 然后访问 http://localhost:8000")


if __name__ == "__main__":
    sys.exit(main())
