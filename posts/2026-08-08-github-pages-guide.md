---
title: 用 GitHub Pages 搭建个人主页
date: 2026-08-08
tags: [教程, GitHub, 建站]
excerpt: 从零开始、免费托管个人主页的完整指南：创建仓库、生成站点、启用 Pages 三步搞定。
---

GitHub Pages 是 GitHub 提供的**免费静态网站托管服务**。这篇文章记录我搭建这个主页的完整过程，也方便你参考。

## 第一步：创建仓库

个人主页的仓库名必须和你的 GitHub 用户名一致，格式是 `用户名.github.io`。

```bash
# 例如用户名为 LunaBright
# 仓库名就是 LunaBright.github.io
```

## 第二步：准备网站文件

本站点的结构如下：

```text
.
├── index.html        # 首页（由 build.py 自动更新“最新文章”）
├── blog/             # 博客列表与文章页（自动生成）
├── posts/            # 文章源文件，写 Markdown 的地方
├── pages/            # 页面内容模板
├── templates/        # 页头 / 页脚共享模板
├── assets/           # 样式、脚本、图标
└── build.py          # 站点生成器
```

写完文章后，运行生成器即可：

```bash
python build.py
```

## 第三步：启用 GitHub Pages

1. 进入仓库的 **Settings → Pages**
2. Source 选择 **Deploy from a branch**
3. Branch 选择 `main`，目录选择 `/ (root)`
4. 点击 **Save**，稍等一分钟即可访问

访问地址就是 `https://用户名.github.io`。

## 几个实用提示

- 仓库里的 `.nojekyll` 空文件可以跳过 Jekyll 构建，纯静态页面部署更快
- 文章更新后记得先运行 `python build.py` 再推送
- 想换域名？在仓库 Settings 的 Custom domain 里配置，并添加一条 CNAME 解析即可

---

以上就是搭建的全部过程。如果你也在折腾自己的小站，欢迎和我交流！✌️

