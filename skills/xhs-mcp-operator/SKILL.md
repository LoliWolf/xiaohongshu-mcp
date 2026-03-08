---
name: xhs-mcp-operator
description: 操作小红书 MCP 服务的技能。包含检查登录、扫码登录、发布图文/视频、搜索帖子、获取帖子详情、获取用户主页、评论、点赞、收藏等能力。支持图文发帖时直接上传图片，或在未提供图片时由客户端自动生成文字配图后继续调用现有 /api/v1/publish 接口，适合日常自动化和纯文案发帖场景。
---

# 小红书 MCP 操作指南

## 概述

本技能提供 Python 脚本 `scripts/xhs_client.py`，用于与本地运行的小红书 MCP 服务交互，默认地址为 `http://localhost:18060`。

如果图文发帖时没有传入 `--images`，脚本会在客户端基于标题和正文自动生成一张本地 PNG 文字配图，再继续复用现有 `/api/v1/publish` 接口发帖。也就是说，后端仍按“有图图文”处理，只是由客户端补图，从而支持更接近“纯文案发帖”的使用体验。

**前提条件**：
- 确保小红书 MCP 服务已运行
- 若要使用自动文字配图，需安装 Pillow：

```bash
python -m pip install Pillow
```

- 如服务不在本机，可通过 `--base-url` 指定地址

```bash
python scripts/xhs_client.py --base-url "http://192.168.1.100:18060" check_login_status
```

## 使用方法

### 1. 账号与登录管理

**检查登录状态**
```bash
python scripts/xhs_client.py check_login_status
```

**获取登录二维码**
```bash
python scripts/xhs_client.py get_login_qrcode
```

获取二维码后，请提示用户使用小红书 App 扫码登录。

**退出登录（删除 Cookies）**
```bash
python scripts/xhs_client.py delete_cookies
```

### 2. 内容发布

**发布流程与规范**：
1. **内容检查**
   - 标题长度必须 ≤ 38（中文字符计 2，英文字符计 1）
   - 正文段落建议使用双换行分隔，语言自然，避免机器翻译感
2. **人工确认**
   - 在执行发布命令前，必须先向用户展示即将发布的标题、正文、图片或自动生成图片信息
   - 必须获得用户明确确认后再继续
   - 不要自动发布
3. **文件传参建议**
   - 建议将标题和正文写入 UTF-8 文本文件后用 `--title-file`、`--content-file` 传入，避免命令行转义和特殊字符问题
4. **图片建议**
   - 有现成配图时，优先传本地绝对路径
   - 未传图片时，客户端会自动生成 1080x1440 的 PNG 文字配图

#### 发布图文笔记

**方式 A：直接上传已有图片**
```bash
python scripts/xhs_client.py publish_content --title "笔记标题" --content "正文内容" --images "C:/path/to/img1.jpg" "C:/path/to/img2.jpg" --tags "美食" "探店" --visibility "公开可见"
```

**方式 B：纯文案发帖，自动生成文字配图**
```bash
python scripts/xhs_client.py publish_content --title "hello 测试一下" --content "朋友们好，这是 OpenClaw 发的测试帖。"
```

**方式 C：通过文件传参，并指定配图样式**
```bash
python scripts/xhs_client.py publish_content --title-file title.txt --content-file content.txt --poster-style warm --poster-footer "测试帖，请勿互动"
```

**可选样式**：
- `minimalist`：默认，简洁留白风格
- `warm`：暖色调风格
- `note`：便签感风格

**说明**：
- 传入 `--images` 时，继续按原有方式直接发图文
- 不传 `--images` 时，客户端自动生成本地 PNG 文字配图并继续发布
- 输出结果会附带是否自动生成图片、生成图片路径、实际发送的图片列表

#### 发布视频笔记

```bash
python scripts/xhs_client.py publish_video --title "视频标题" --content "正文内容" --video "C:/path/to/video.mp4" --tags "日常" "Vlog"
```

或：

```bash
python scripts/xhs_client.py publish_video --title-file title.txt --content-file content.txt --video "C:/path/to/video.mp4" --tags "日常" "Vlog"
```

### 3. 内容浏览与搜索

**获取首页推荐**
```bash
python scripts/xhs_client.py list_feeds
```

**搜索笔记**
```bash
python scripts/xhs_client.py search_feeds --keyword "搜索关键词" --sort_by "最多点赞" --note_type "图文"
```

**获取笔记详情（含评论）**
```bash
python scripts/xhs_client.py get_feed_detail --feed_id "笔记ID" --xsec_token "安全令牌" --load_all_comments
```

### 4. 用户信息

**获取用户主页**
```bash
python scripts/xhs_client.py user_profile --user_id "用户ID" --xsec_token "安全令牌"
```

### 5. 互动操作

**发表评论**
```bash
python scripts/xhs_client.py post_comment_to_feed --feed_id "笔记ID" --xsec_token "安全令牌" --content "评论内容"
```

**回复评论**
```bash
python scripts/xhs_client.py reply_comment_in_feed --feed_id "笔记ID" --xsec_token "安全令牌" --comment_id "目标评论ID" --content "回复内容"
```

**点赞 / 取消点赞**
```bash
python scripts/xhs_client.py like_feed --feed_id "笔记ID" --xsec_token "安全令牌"
python scripts/xhs_client.py like_feed --feed_id "笔记ID" --xsec_token "安全令牌" --unlike
```

**收藏 / 取消收藏**
```bash
python scripts/xhs_client.py favorite_feed --feed_id "笔记ID" --xsec_token "安全令牌"
python scripts/xhs_client.py favorite_feed --feed_id "笔记ID" --xsec_token "安全令牌" --unfavorite
```

## 注意事项

1. `xsec_token` 用于详情、评论、点赞、收藏等操作，可从 `list_feeds` 或 `search_feeds` 返回结果中获取
2. 发布图文时推荐使用本地绝对路径图片；如果要走自动文字配图，确保环境可用 Pillow 且系统存在可显示中文的字体
3. `like_feed` 与 `favorite_feed` 通过 MCP `/mcp` 端点调用，其他大多数功能通过 HTTP API 调用，脚本已统一封装
4. 自动文字配图只是客户端补图方案，不代表服务端支持真正的无图图文发布
