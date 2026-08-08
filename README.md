# LunaBright 个人主页

一个免费托管在 **GitHub Pages** 上的个人主页 + 博客站点，用于展示自己和记录技术笔记、学习心得与生活碎片。

## 技术栈

- 纯 HTML / CSS / JavaScript，零构建依赖，部署零风险
- `build.py`（仅用 Python 标准库）把 Markdown 文章渲染成静态页面
- GitHub Pages 免费托管，支持浅色 / 深色主题、响应式布局、Atom 订阅（`feed.xml`）

## 目录结构

```text
.
├── index.html          # 首页（生成，build.py 自动更新“最新文章”）
├── blog/               # 博客列表与文章页（全部自动生成）
├── posts/              # ★ 文章源文件：在这里写 Markdown
├── pages/              # 首页 / 博客列表 / 404 页面内容模板
├── templates/          # 页头、页脚共享模板
├── assets/
│   ├── css/style.css   # 全部样式（主题色也在这里改）
│   ├── js/main.js      # 主题切换、移动端菜单、回到顶部
│   └── favicon.svg
├── build.py            # ★ 站点生成器
├── feed.xml            # Atom 订阅源（生成）
└── README.md
```

## 本地预览

需要 Python 3.8+（已安装则跳过第一步）。

```bash
python build.py
python -m http.server 8000
```

浏览器打开 <http://localhost:8000> 即可查看。

## 写一篇新文章

1. 在 `posts/` 目录新建文件，命名为 `YYYY-MM-DD-英文短标题.md`；
2. 在文件开头写基本信息：

```markdown
---
title: 我的第一篇文章
date: 2026-08-08
tags: [随笔, 教程]
excerpt: 可选。不写的话会自动截取正文开头作为摘要。
---
```

3. 正文用 Markdown 书写，支持：标题、段落、**加粗**、*斜体*、`行内代码`、代码块（``` 围栏）、无序 / 有序列表、引用、分割线、链接和图片；
4. 运行 `python build.py` 生成页面；
5. 提交并推送：

```bash
git add -A
git commit -m "添加新文章"
git push
```

## 部署到 GitHub Pages

### 前提

- 有一个 GitHub 账号（本文以 `LunaBright` 为例）

### 步骤

1. 在 GitHub 上创建仓库，仓库名必须与用户名一致：

   ```text
   LunaBright.github.io
   ```

   （仓库设为 Public）

2. 关联远程仓库并推送：

   ```bash
   git remote add origin https://github.com/LunaBright/LunaBright.github.io.git
   git push -u origin main
   ```

3. 在仓库页面进入 **Settings → Pages**：

   - Source 选择 **Deploy from a branch**
   - Branch 选择 `main`，目录选择 `/ (root)`
   - 点击 **Save**

4. 等一分钟左右，访问 `https://lunabright.github.io` 即可看到主页。

> 如果 GitHub 用户名不是 `LunaBright`，把仓库名、`build.py` 顶部的 `SITE_URL` 以及模板里的 GitHub 链接一并替换。

## 自定义网站

| 想改什么 | 改哪里 |
| --- | --- |
| 自我介绍、头像、技能、联系方式 | `pages/home.html` |
| 站点名称、站点 URL、邮箱 | `build.py` 顶部配置 |
| 导航栏 / 页脚的链接 | `templates/header.html`、`templates/footer.html` |
| 主题配色、字体 | `assets/css/style.css` 顶部的 CSS 变量 |
| 博客列表页的介绍文字 | `pages/blog.html` |

头像目前是 CSS 生成的「LB」圆形图标，想换成自己的照片时，把 `pages/home.html` 里的头像块替换成 `<img class="avatar" src="assets/images/me.jpg" alt="我的照片">` 即可（图片放进 `assets/images/` 目录）。

## 常见问题

**改了文章但线上没变化？**
先运行 `python build.py` 重新生成页面，再 `git push`。

**换电脑后怎么继续写？**
装好 Python 3.8+，`git clone` 这个仓库，然后按「本地预览」步骤操作即可。

**想用自己的域名？**
在 **Settings → Pages → Custom domain** 里填写域名，并在 DNS 里添加一条 CNAME 记录指向 `用户名.github.io`。

**为什么仓库里有个空的 `.nojekyll` 文件？**
它告诉 GitHub Pages 跳过 Jekyll 构建，直接托管纯静态文件，加快部署。

