---
name: xhs-mcp-operator
description: 操作小红书 MCP 服务的技能。包含所有小红书操作功能：检查登录、扫码登录、发布图文/视频、搜索帖子、获取帖子详情、获取用户主页、评论、点赞、收藏等。当用户要求操作小红书或调用小红书 MCP 时使用此技能。
---

# 小红书 MCP 操作指南 (Xhs Mcp Operator)

## 概述

本技能提供了一个 Python 脚本 `scripts/xhs_client.py`，用于与本地运行的小红书 MCP 服务（默认端口 18060）进行交互。通过该脚本，你可以执行小红书的各种操作，包括内容发布、数据获取和互动操作。

**前提条件**：确保小红书 MCP 服务已经运行。默认连接本地 `http://localhost:18060`，如果 MCP 服务在其他地址，可以通过 `--base-url` 参数指定。

## 使用方法

使用 Python 运行 `scripts/xhs_client.py` 脚本，并传入相应的子命令和参数。
所有命令都支持通过 `--base-url` 指定 MCP 服务地址，例如：
```bash
python scripts/xhs_client.py --base-url "http://192.168.1.100:18060" check_login_status
```

### 1. 账号与登录管理

**检查登录状态**
```bash
python scripts/xhs_client.py check_login_status
```

**获取登录二维码**
```bash
python scripts/xhs_client.py get_login_qrcode
```
*注意：获取到二维码后，请提示用户使用小红书 App 扫码登录。*

**退出登录（删除 Cookies）**
```bash
python scripts/xhs_client.py delete_cookies
```

### 2. 内容发布

**发布流程与规范**：
1. **内容检查**：
   - 标题长度必须 ≤ 38（中文字符计2，英文字符计1）。如果超长，自动生成符合长度要求的新标题，保持语义一致。
   - 正文段落之间使用双换行分隔，语言自然，避免机器翻译感。
2. **用户确认**：
   - 在执行发布命令前，必须向用户展示即将发布的内容（标题、正文、图片），获得明确确认后再继续。
   - 绝不自动发布。
3. **写入临时文件**：
   - 为了避免命令行参数过长或特殊字符导致的问题，建议将标题和正文写入临时 UTF-8 文本文件，然后通过脚本读取（如果脚本支持），或者在调用脚本时小心处理转义。

**发布图文笔记**
```bash
# 直接传参
python scripts/xhs_client.py publish_content --title "笔记标题" --content "正文内容" --images "/path/to/img1.jpg" "/path/to/img2.jpg" --tags "美食" "探店" --visibility "公开可见"

# 通过文件传参（推荐，避免特殊字符问题）
python scripts/xhs_client.py publish_content --title-file title.txt --content-file content.txt --images "/path/to/img1.jpg" "/path/to/img2.jpg" --tags "美食" "探店"
```

**发布视频笔记**
```bash
# 直接传参
python scripts/xhs_client.py publish_video --title "视频标题" --content "正文内容" --video "/path/to/video.mp4" --tags "日常" "Vlog"

# 通过文件传参（推荐，避免特殊字符问题）
python scripts/xhs_client.py publish_video --title-file title.txt --content-file content.txt --video "/path/to/video.mp4" --tags "日常" "Vlog"
```

### 3. 内容浏览与搜索

**获取首页推荐 (Feeds)**
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

**点赞/取消点赞**
```bash
# 点赞
python scripts/xhs_client.py like_feed --feed_id "笔记ID" --xsec_token "安全令牌"

# 取消点赞
python scripts/xhs_client.py like_feed --feed_id "笔记ID" --xsec_token "安全令牌" --unlike
```

**收藏/取消收藏**
```bash
# 收藏
python scripts/xhs_client.py favorite_feed --feed_id "笔记ID" --xsec_token "安全令牌"

# 取消收藏
python scripts/xhs_client.py favorite_feed --feed_id "笔记ID" --xsec_token "安全令牌" --unfavorite
```

## 注意事项

1. **xsec_token**：在进行获取详情、评论、点赞、收藏等操作时，必须提供 `xsec_token`。该令牌可以从 `list_feeds` 或 `search_feeds` 的返回结果中获取。
2. **图片/视频路径**：发布内容时，推荐使用本地绝对路径。
3. **MCP 协议调用**：`like_feed` 和 `favorite_feed` 是通过向 MCP 服务的 `/mcp` 端点发送 JSON-RPC 请求实现的，其他功能通过 HTTP API 实现。脚本已将这些差异封装，统一通过命令行调用。
