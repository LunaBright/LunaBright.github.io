# LunaBright 个人主页

一个免费托管在 **GitHub Pages** 上的个人主页 + 博客，支持**网页端在线写作**（Pages CMS）、分类与标签、全文搜索、背景图/头像在线更换、LaTeX 公式、Markdown 表格和带图注的图片排版，以及 giscus 评论区。

## 技术栈

- 纯 HTML / CSS / JavaScript，零构建依赖
- `build.py`（Python 3.8+ 标准库）把 Markdown 文章渲染成静态页面
- **Pages CMS**（app.pagescms.org）提供网页后台，登录 GitHub 即可写文章、改设置
- GitHub Actions 自动构建并部署到 GitHub Pages
- KaTeX 渲染公式、giscus 提供评论区

## 目录结构

```text
.
├── .pages.yml             # ★ Pages CMS 后台配置（文章字段、站点设置、图片上传）
├── .github/workflows/     # GitHub Actions 自动构建部署
├── data/site.json         # ★ 站点设置：名称、头像、背景图、简介、评论区等
├── posts/                 # ★ 文章源文件（Markdown，后台写文章会自动保存到这里）
├── pages/                 # 首页 / 博客页 / 404 页面模板
├── templates/             # 页头、页脚共享模板
├── assets/                # 样式、脚本、默认背景图与头像
│   └── images/            # 默认 background.svg / avatar.svg
├── media/images/          # 后台上传的图片（自动创建）
├── build.py               # 站点生成器
├── index.html             # 首页（build.py 自动生成）
├── blog/                  # 博客列表与文章页（自动生成）
└── feed.xml               # Atom 订阅（自动生成）
```

## 一、在线写文章（核心流程）

1. 打开 <https://app.pagescms.org>，用你的 GitHub 账号登录。
2. 选择 `LunaBright/LunaBright.github.io` 仓库（首次可能需要授权 Pages CMS 访问）。
3. 左侧「博客文章」→ 新建文章：
   - 填写**标题、分类、标签、日期**，可选封面图和摘要；
   - 勾选**草稿**则暂时不发布；
   - 正文是富文本编辑器，也直接支持 Markdown 语法。
4. 点「保存」——文件会以 Markdown 形式提交到仓库，GitHub Actions 自动构建并发布，等一两分钟即可在 `https://lunabright.github.io` 看到新文章。

后台还提供「**重新构建并部署**」按钮，随时手动触发一次部署。

### 正文支持的语法

| 功能 | 写法 | 说明 |
| --- | --- | --- |
| 标题 | `## 二级标题` | `#` 到 `######` |
| 列表 | `- 项目` / `1. 项目` | 无序 / 有序 |
| 代码 | `` `行内代码` `` / ```` ```代码块``` ```` | 代码块可标注语言 |
| 引用 | `> 引用内容` | |
| 链接 | `[文字](https://地址)` | |
| 表格 | `\| 列 \| 列 \|` | 标准 Markdown 表格，支持对齐 |
| 公式 | `$E=mc^2$` 或 `$$...$$` | LaTeX 语法，前端 KaTeX 渲染 |
| 图片 | `![说明](图片地址)` | 直接插入；后台粘贴图片会自动上传到 `media/images/` |
| 图片排版 | `![说明](地址 "width:60%,align:center,figcaption:图注文字")` | `width` 支持百分比或像素；`align` 支持 `left` / `center` / `right` |
| 粗体/斜体/删除线 | `**粗**` `*斜*` `~~删~~` | |

## 二、更换背景图和头像（网页上操作）

打开后台 → 「**站点设置**」：

- **头像**：点字段里的图片按钮，上传或选择一张图，保存即可全站生效；
- **背景图**：同样操作，上传自己的照片（自然风景、极简插画都可以），保存后全站背景立即更换；
- 上传的图片会存到 `media/images/`，自动生成 `/media/images/xxx` 链接。

默认背景是仓库里手绘的极简暮色群山 SVG（`assets/images/background.svg`），头像默认是「LB」字母图标（`assets/images/avatar.svg`），在后台换成你自己的照片即可。

## 三、评论区（giscus）

评论区用 giscus（GitHub Discussions 驱动，免费、无广告）。启用需要三步：

1. 到 <https://github.com/apps/giscus> 安装 giscus App，并允许它访问 `LunaBright/LunaBright.github.io`；
2. 在仓库 **Settings → General → Discussions** 勾选启用 Discussions，并在 Discussions 里创建一个分类（如 Announcements）；
3. 打开 <https://giscus.app>，按页面提示选择仓库和分类，把生成的 **repo_id** 和 **category_id** 填到后台「站点设置 → 评论设置」里保存。

填好后再发一篇文章，文章底部就会出现评论区。

## 四、如何按自己的需求修改其它部分

| 想改什么 | 去哪里改 |
| --- | --- |
| 站点名称、简介、作者、邮箱、GitHub、头像、背景图、首页大段介绍、技能标签、联系方式 | 后台「**站点设置**」（`data/site.json`） |
| 文章分类（技术/生活/随笔） | 后台文章字段；想增删分类改 `.pages.yml` 里 `category` 的 `options` |
| 导航菜单、页脚链接 | `templates/header.html`、`templates/footer.html` |
| 首页区块布局（英雄区、关于、技能、联系） | `pages/home.html` |
| 博客页顶部介绍文字 | `pages/blog.html` |
| 主题颜色、字体、圆角、阴影 | `assets/css/style.css` 顶部的 CSS 变量（`--accent` 等） |
| 文章页排版细节 | `assets/css/style.css` 中 `.prose` 部分 |
| 站点 URL、feed 域名 | `data/site.json` 的 `site_url` |
| 评论仓库等 | 后台「站点设置 → 评论设置」 |

**主题色**：改 `assets/css/style.css` 里 `:root` 的 `--accent`（主色）和 `--accent-2`（点缀色），深色主题在 `[data-theme="dark"]` 里同样有一份。

**导航**：`templates/header.html` 里 `<div class="nav-links">` 中的链接就是导航项，增删即可；页脚同理在 `templates/footer.html`。

**首页**：`pages/home.html` 中「关于我」「技能与兴趣」「联系我」三块内容都来自站点设置，其它布局想大改可以直接编辑这个文件（内容是 HTML 模板，`{{TOKEN}}` 会被 build.py 替换）。

## 五、部署到线上（首次）

仓库文件推送到 GitHub 后，还需要做一次设置：

1. 进入仓库 **Settings → Pages**；
2. **Source / Build and deployment** 选择 **GitHub Actions**（这一步会创建 `github-pages` 部署环境，必须选它，不能再用 "Deploy from a branch"）；
3. 等 Actions 跑完，访问 `https://lunabright.github.io`。

之后每次在后台保存文章，都会自动触发构建部署，无需再手动操作。

## 六、本地开发

需要 Python 3.8+：

```bash
python build.py
python -m http.server 8000
```

浏览器打开 <http://localhost:8000> 即可预览。

生成到独立目录（和 GitHub Actions 一致）：

```bash
python build.py --out _site
```

## 常见问题

**后台保存了但线上没变化？**
检查仓库 Actions 页有没有跑成功；GitHub Pages 设置是否选的是「GitHub Actions」。

**后台上传图片报「Resource not accessible by integration」？**
这是 Pages CMS 的 GitHub 应用缺少仓库写入权限。修复：GitHub → **Settings → Applications** → 找到 **Pages CMS** → **Configure** → 在 Repository access 里把 `LunaBright/LunaBright.github.io` 勾上（或选 All repositories），保存后再回后台重试。

**后台上传图片报 413 / Failed to upload file？**
上传的文件太大（服务端对单次上传体积有限制）。把图片压缩到 1MB 以内再传；如果一定要用大图，可以到 GitHub 仓库页面 **Add file → Upload files**，把图片直接传到 `media/images/` 目录，然后在文章里引用 `/media/images/文件名`。

**文章里图片显示为裂开图标？**
通常是图片上传失败、文章里引用的 `/media/images/...` 文件并不存在。检查文章 Markdown 里的图片地址，确认对应文件已经真的在仓库 `media/images/` 里（上一问的方法）。本站自带图片（如 `/assets/images/background.svg`）在线上是正常的。

**想用自己域名？**
在仓库 **Settings → Pages → Custom domain** 填写域名，并按提示在 DNS 添加 CNAME 记录。

**公式没渲染？**
公式用美元符号包裹：行内 `$...$`、块级 `$$...$$`。如果浏览器离线或 CDN 被墙，需要能访问 cdn.jsdelivr.net。
