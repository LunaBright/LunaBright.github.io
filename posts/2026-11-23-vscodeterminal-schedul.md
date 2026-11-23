---
title: vscode的插件探索——Terminal Scheduler
category: 技术
tags:
  - vscode插件
  - codex
  - 定时任务
  - Terminal Scheduler
date: 2026-11-23
cover: /media/images/snipaste2026-11-2321-08-47.png
excerpt: 使用vscode的插件Terminal Scheduler设置定时发送消息给终端中的codex对话（或普通的终端）。可以保证额度恢复时尽快继续任务。
draft: false
---
> 适用于使用**codex时额度恢复**时间无法操作的情况。
>
> 注意：设定任务期间vscode、codex以及终端等的网络连接要稳定，否则会发送失败。

## 使用方法

1. 在项目根目录下创建`.vscode/terminal-schedule.jsonl`文件
2. 在该文件中填写定时发送任务的内容详情，示例如下：

```jsonl

{"target": "my-codex", "datetime": "2026-11-23T02:35:00", "text": "继续\r", "enabled": true}

```

参数：

- target：需要发送消息的终端名称。建议重命名为一个独特的终端，能够让插件精准查找。若该名称的终端不存在则会自动新建。
- datetime：发送消息的时间，格式依照参考即可。
- text：发送给终端的消息内容。`\r`表示换行或回车，`\n`表示同样的含义。但是具体作用需要在vscode中实际测试，有时是换行，有时是回车发送的效果。

像这样的一行内容就代表一个定时发送任务，可以同时设置多行，在规定的时间发送。

3.加载配置文件：在vscode中`ctrl+shift+p`，然后在搜索框中输入`Terminal Scheduler: Reload Config`，点击后回车，确认右下角状态栏中出`Sched: 1 pending`或类似的字样，说明设置成功。后续设定新任务并保存配置文件后会同样出现类似的字样。若没有出现，可以尝试再次加载配置文件。图示如下（当前没有设置定时发送任务）：

![image.png](/media/images/image-11.png)

开始使用时可以先设定一个最近的时间测试一下功能是否正常。