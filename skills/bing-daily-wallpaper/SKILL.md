---
name: bing-daily-wallpaper
description: 下载 Bing 中国区每日壁纸的技能。提供脚本请求 https://cn.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=zh-CN，解析当日壁纸信息，继续下载真实图片，并返回 copyright、标题、图片地址与本地保存路径。适合在需要获取 Bing 每日壁纸并落盘到指定目录时使用。
---

# Bing 每日壁纸下载

使用 `scripts/fetch_bing_wallpaper.py` 下载 Bing 中国区当日壁纸。

## 用法

```bash
python scripts/fetch_bing_wallpaper.py "C:/path/to/output"
```

脚本会：
1. 请求 Bing 每日壁纸 API
2. 解析返回的首张图片信息
3. 下载真实图片到指定目录
4. 输出 JSON 结果

## 输出字段

- `copyright`
- `copyright_link`
- `title`
- `startdate`
- `image_url`
- `saved_path`

## 注意事项

- 运行环境需要安装 `requests`
- `output_dir` 不存在时会自动创建
- 文件名格式为 `bing_wallpaper_日期.扩展名`
