#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py —— 个人主页静态站点生成器

功能：
  1. 把 posts/*.md 渲染成 blog/posts/*.html
  2. 更新 blog/index.html 博客列表
  3. 更新 index.html 首页“最新文章”区块
  4. 生成 feed.xml Atom 订阅源

用法：
  python build.py
"""

import html as html_mod
import re
import sys
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parent

# ============ 站点配置（按需修改） ============
SITE_NAME = "LunaBright"
SITE_DESC = "LunaBright 的个人主页：技术笔记、学习心得与生活记录"
SITE_URL = "https://lunabright.github.io"
AUTHOR = "LunaBright"
GITHUB_URL = "https://github.com/LunaBright"
EMAIL = "2154626568@qq.com"
HOME_RECENT = 3  # 首页“最新文章”数量
# ==============================================

POSTS_DIR = ROOT / "posts"
PAGES_DIR = ROOT / "pages"
TEMPLATES_DIR = ROOT / "templates"
BLOG_OUT = ROOT / "blog"
POSTS_OUT = BLOG_OUT / "posts"


# ---------- 小工具 ----------

def log(msg):
    print(msg)


def write_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    log("  生成 %s" % path.relative_to(ROOT).as_posix())


def render_template(name, tokens):
    """读取 templates/ 下的模板并替换 {{TOKEN}}。"""
    text = (TEMPLATES_DIR / name).read_text(encoding="utf-8")
    for key, value in tokens.items():
        text = text.replace("{{%s}}" % key, value)
    return text


def render_page(name, tokens):
    """读取 pages/ 下的页面片段并替换 {{BASE}} 等 token。"""
    text = (PAGES_DIR / name).read_text(encoding="utf-8")
    for key, value in tokens.items():
        text = text.replace("{{%s}}" % key, value)
    return text


def date_display(date_str):
    """2026-08-08 -> 2026 年 8 月 8 日"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return "%d 年 %d 月 %d 日" % (dt.year, dt.month, dt.day)
    except ValueError:
        return date_str


# ---------- 极简 Markdown 解析 ----------

def md_inline(text):
    """行内语法：代码、图片、链接、加粗、斜体、删除线。"""
    text = html_mod.escape(text, quote=False)

    # 行内代码
    text = re.sub(r"`([^`\n]+)`", lambda m: "<code>%s</code>" % m.group(1), text)

    # 图片
    text = re.sub(
        r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)",
        lambda m: '<img src="%s" alt="%s" loading="lazy">'
        % (safe_url(m.group(2)), m.group(1)),
        text,
    )

    # 链接
    text = re.sub(
        r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)",
        lambda m: '<a href="%s" title="%s">%s</a>'
        % (safe_url(m.group(2)), m.group(3) or "", m.group(1)),
        text,
    )

    # 加粗
    text = re.sub(r"\*\*([^*\n]+)\*\*", r"<strong>\1</strong>", text)
    # 斜体
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", text)
    # 删除线
    text = re.sub(r"~~([^~\n]+)~~", r"<del>\1</del>", text)
    return text


def safe_url(url):
    url = url.strip()
    if url.lower().startswith(("javascript:", "vbscript:", "data:")):
        return "#"
    return url


def md_to_html(md):
    """极简 Markdown 块级解析。支持标题、代码块、引用、列表、分割线、段落。"""
    lines = md.split("\n")
    blocks = []  # (type, content)
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
            i += 1  # 跳过结束围栏
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

        # 段落
        buf = []
        block_start = re.compile(
            r"^\s*(?:```|#{1,6}\s|>|[-*+]\s+|\d+[.)]\s+|-{3,}\s*$|\*{3,}\s*$)"
        )
        while i < n and lines[i].strip():
            if buf and block_start.match(lines[i]):
                break
            buf.append(lines[i].strip())
            i += 1
        blocks.append(("p", md_inline(" ".join(buf))))

    # 渲染
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
        elif typ == "p":
            out.append("<p>%s</p>" % content)
    return "\n".join(out)


# ---------- 文章读取 ----------

FRONT_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.S)


def parse_front_matter(text):
    """解析 front matter（标题 / 日期 / 标签 / 摘要），返回 (meta, body)。"""
    meta = {}
    body = text
    m = FRONT_RE.match(text)
    if m:
        body = text[m.end():]
        for line in m.group(1).splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                meta[key.strip().lower()] = value.strip()
    raw_tags = meta.get("tags", "")
    raw_tags = raw_tags.strip().strip("[]").strip()
    meta["tags"] = [t.strip().strip("\"'") for t in raw_tags.split(",") if t.strip()]
    return meta, body.strip()


def read_posts():
    posts = []
    if not POSTS_DIR.exists():
        return posts
    for md_file in sorted(POSTS_DIR.glob("*.md")):
        meta, body = parse_front_matter(md_file.read_text(encoding="utf-8"))
        slug = md_file.stem
        title = meta.get("title") or slug
        date = meta.get("date") or slug[:10]
        tags = meta.get("tags") or []
        content_html = md_to_html(body)
        plain = re.sub(r"<[^>]+>", " ", content_html)
        plain = re.sub(r"\s+", " ", plain).strip()
        excerpt = meta.get("excerpt") or plain[:120].rstrip()
        minutes = max(1, round(len(plain) / 500))
        posts.append(
            {
                "slug": slug,
                "title": title,
                "date": date,
                "date_display": date_display(date),
                "tags": tags,
                "excerpt": excerpt,
                "content_html": content_html,
                "minutes": minutes,
            }
        )
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


# ---------- 组件生成 ----------

def tags_html(tags):
    return "".join('<span class="tag">%s</span>' % html_mod.escape(t) for t in tags)


def post_card(post, base):
    return (
        '<article class="post-card reveal">\n'
        '  <a class="post-card-link" href="%sblog/posts/%s.html">\n'
        '    <div class="post-card-meta"><time datetime="%s">%s</time><span>·</span><span>约 %d 分钟</span></div>\n'
        '    <h3 class="post-card-title">%s</h3>\n'
        '    <p class="post-card-excerpt">%s…</p>\n'
        '    <div class="post-card-tags">%s</div>\n'
        "  </a>\n"
        "</article>"
    ) % (
        base,
        post["slug"],
        post["date"],
        post["date"],
        post["minutes"],
        html_mod.escape(post["title"]),
        html_mod.escape(post["excerpt"]),
        tags_html(post["tags"]),
    )


def post_row(post, base):
    return (
        '<article class="post-list-item reveal">\n'
        '  <time class="post-list-date" datetime="%s">%s</time>\n'
        '  <div class="post-list-main">\n'
        '    <h2 class="post-list-title"><a href="%sblog/posts/%s.html">%s</a></h2>\n'
        '    <p class="post-list-excerpt">%s…</p>\n'
        '    <div class="post-list-tags">%s</div>\n'
        "  </div>\n"
        "</article>"
    ) % (
        post["date"],
        post["date"],
        base,
        post["slug"],
        html_mod.escape(post["title"]),
        html_mod.escape(post["excerpt"]),
        tags_html(post["tags"]),
    )


def page_shell(title, desc, base, body, home_active="", blog_active=""):
    header = render_template(
        "header.html",
        {
            "TITLE": title,
            "DESC": desc,
            "BASE": base,
            "HOME_ACTIVE": home_active,
            "BLOG_ACTIVE": blog_active,
        },
    )
    footer = render_template("footer.html", {"BASE": base})
    return header + body + footer


# ---------- 页面构建 ----------

def build_home(posts):
    log("构建首页 index.html")
    recent = posts[:HOME_RECENT]
    cards = "\n".join(post_card(p, "") for p in recent)
    body = render_page("home.html", {"BASE": ""}).replace("<!-- RECENT_POSTS -->", cards)
    write_text(ROOT / "index.html", page_shell(SITE_NAME + " · " + SITE_DESC, SITE_DESC, "", body, home_active=" active"))


def build_blog_index(posts):
    log("构建博客列表 blog/index.html")
    rows = "\n".join(post_row(p, "../") for p in posts)
    body = render_page("blog.html", {"BASE": "../"}).replace("<!-- POST_LIST -->", rows)
    write_text(BLOG_OUT / "index.html", page_shell("博客 · " + SITE_NAME, "LunaBright 的博客文章列表", "../", body, blog_active=" active"))


def build_post_pages(posts):
    log("构建文章页面 blog/posts/")
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
                parts.append('<span></span>')
            if nxt:
                parts.append(
                    '<a class="pager-next" href="%s.html"><span class="pager-label">下一篇 →</span>%s</a>'
                    % (nxt["slug"], html_mod.escape(nxt["title"]))
                )
            else:
                parts.append("<span></span>")
            pager = '<nav class="post-pager" aria-label="上一篇/下一篇">%s</nav>' % "".join(parts)

        body = (
            '<article class="post">\n'
            '  <div class="container container-narrow">\n'
            '    <header class="post-header">\n'
            '      <p class="page-eyebrow"><a href="../index.html">← 返回博客</a></p>\n'
            '      <h1 class="post-title">%s</h1>\n'
            '      <div class="post-meta">\n'
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
        ) % (
            html_mod.escape(post["title"]),
            post["date"],
            post["date_display"],
            post["minutes"],
            tags_html(post["tags"]),
            post["content_html"],
            pager,
        )
        write_text(
            POSTS_OUT / (post["slug"] + ".html"),
            page_shell(post["title"] + " · " + SITE_NAME, post["excerpt"], "../../", body, blog_active=" active"),
        )


def build_404():
    log("构建 404 页面")
    body = render_page("404.html", {"BASE": "./"})
    write_text(ROOT / "404.html", page_shell("页面走丢了 · " + SITE_NAME, "404 页面", "./", body))


def build_feed(posts):
    log("生成 Atom 订阅源 feed.xml")
    entries = []
    for p in posts:
        url = "%s/blog/posts/%s.html" % (SITE_URL, p["slug"])
        entries.append(
            "  <entry>\n"
            "    <title>%s</title>\n"
            '    <link href="%s"/>\n'
            '    <id>%s</id>\n'
            "    <updated>%sT00:00:00+08:00</updated>\n"
            "    <author><name>%s</name></author>\n"
            '    <summary>%s</summary>\n'
            '    <content type="html">%s</content>\n'
            "  </entry>" % (
                xml_escape(p["title"]),
                xml_escape(url),
                xml_escape(url),
                p["date"],
                xml_escape(AUTHOR),
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
        '  <updated>%sT00:00:00+08:00</updated>\n'
        "  <author><name>%s</name><email>%s</email></author>\n"
        "  <id>%s</id>\n"
        "%s\n"
        "</feed>\n"
    ) % (
        xml_escape(SITE_NAME),
        xml_escape(SITE_DESC),
        SITE_URL,
        SITE_URL,
        posts[0]["date"] if posts else datetime.now().strftime("%Y-%m-%d"),
        xml_escape(AUTHOR),
        xml_escape(EMAIL),
        SITE_URL + "/",
        "\n".join(entries),
    )
    write_text(ROOT / "feed.xml", feed)


def main():
    print("=" * 48)
    print("  %s 站点生成器" % SITE_NAME)
    print("=" * 48)
    posts = read_posts()
    print("共读取 %d 篇文章\n" % len(posts))
    build_home(posts)
    build_blog_index(posts)
    build_post_pages(posts)
    build_404()
    build_feed(posts)
    print("\n完成！用下面命令在本地预览：")
    print("  python -m http.server 8000")
    print("  然后浏览器打开 http://localhost:8000")


if __name__ == "__main__":
    sys.exit(main())
