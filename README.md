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
