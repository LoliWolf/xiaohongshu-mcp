import argparse
import json
import os
import sys
import tempfile
import textwrap
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

BASE_URL = "http://localhost:18060"
POSTER_SIZE = (1080, 1440)
DEFAULT_POSTER_STYLE = "minimalist"
POSTER_STYLES = {
    "minimalist": {
        "background": "#FFF9F2",
        "title_color": "#1F1F1F",
        "body_color": "#444444",
        "muted_color": "#8E8E93",
        "accent_color": "#FF2442",
        "divider_color": "#E8DED4",
    },
    "warm": {
        "background": "#FFF4EC",
        "title_color": "#5C2E1F",
        "body_color": "#7A4A34",
        "muted_color": "#A06F5B",
        "accent_color": "#FF6B4A",
        "divider_color": "#EBC9BA",
    },
    "note": {
        "background": "#FFFDF7",
        "title_color": "#2F2A26",
        "body_color": "#4B433D",
        "muted_color": "#8A8078",
        "accent_color": "#D97706",
        "divider_color": "#E9DDC7",
    },
}

def make_request(method, path, data=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}

    if data is not None:
        data = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            return json.loads(error_body)
        except json.JSONDecodeError:
            return {"error": error_body, "code": e.code}
    except urllib.error.URLError as e:
        return {"error": str(e.reason), "code": "CONNECTION_ERROR"}


def call_mcp_tool(tool_name, arguments):
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments,
        },
        "id": 1,
    }
    return make_request("POST", "/mcp", payload)


def exit_with_error(message):
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def read_text_arg(direct_value, file_path, field_name):
    value = direct_value
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                value = file.read().strip()
        except OSError as exc:
            exit_with_error(f"Failed to read {field_name} file '{file_path}': {exc}")
    return value.strip() if isinstance(value, str) else value


def normalize_newlines(text):
    if not isinstance(text, str):
        return text
    text = text.replace('\\n', '\n')
    text = text.replace('\r\n', '\n')
    text = text.replace('\r', '\n')
    return text


def require_pillow():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        exit_with_error(
            "Pillow is required to auto-generate a text poster when --images is omitted. "
            "Install it with: python -m pip install Pillow"
        )
    return Image, ImageDraw, ImageFont


def get_font_candidates():
    windows_dir = os.environ.get("WINDIR", r"C:\Windows")
    return [
        os.path.join(windows_dir, "Fonts", "msyh.ttc"),
        os.path.join(windows_dir, "Fonts", "msyhbd.ttc"),
        os.path.join(windows_dir, "Fonts", "simhei.ttf"),
        os.path.join(windows_dir, "Fonts", "simsun.ttc"),
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/arphic/ukai.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]


def load_font(ImageFont, size, bold=False):
    font_candidates = get_font_candidates()
    preferred = []
    fallback = []

    for path in font_candidates:
        lowered = os.path.basename(path).lower()
        if bold and ("bd" in lowered or "bold" in lowered):
            preferred.append(path)
        elif not bold:
            preferred.append(path)
        else:
            fallback.append(path)

    for path in preferred + fallback:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue

    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def text_width(draw, text, font):
    if not text:
        return 0
    left, _, right, _ = draw.textbbox((0, 0), text, font=font)
    return right - left


def wrap_text(draw, text, font, max_width):
    if not text:
        return []

    wrapped_lines = []
    for paragraph in text.splitlines() or [text]:
        clean = paragraph.strip()
        if not clean:
            wrapped_lines.append("")
            continue

        current = ""
        for char in clean:
            candidate = current + char
            if current and text_width(draw, candidate, font) > max_width:
                wrapped_lines.append(current)
                current = char
            else:
                current = candidate
        if current:
            wrapped_lines.append(current)

    return wrapped_lines


def fit_lines(draw, text, font, max_width, max_lines, ellipsis=False):
    lines = wrap_text(draw, text, font, max_width)
    if len(lines) <= max_lines:
        return lines

    trimmed = lines[:max_lines]
    if ellipsis and trimmed:
        while trimmed[-1] and text_width(draw, trimmed[-1] + "…", font) > max_width:
            trimmed[-1] = trimmed[-1][:-1]
        trimmed[-1] = (trimmed[-1] or "") + "…"
    return trimmed


def line_height(draw, font):
    _, top, _, bottom = draw.textbbox((0, 0), "中文Aa", font=font)
    return bottom - top


def render_multiline(draw, lines, position, font, fill, spacing):
    x, y = position
    step = line_height(draw, font) + spacing
    for index, line in enumerate(lines):
        draw.text((x, y + index * step), line, font=font, fill=fill)
    return y + len(lines) * step - spacing if lines else y


def build_footer_text(custom_footer):
    if custom_footer:
        return custom_footer
    return f"OpenClaw · {datetime.now().strftime('%Y-%m-%d')}"


def generate_text_poster(title, content, style_name, footer_text=None, size=POSTER_SIZE):
    Image, ImageDraw, ImageFont = require_pillow()

    style = POSTER_STYLES.get(style_name, POSTER_STYLES[DEFAULT_POSTER_STYLE])
    width, height = size
    image = Image.new("RGB", size, style["background"])
    draw = ImageDraw.Draw(image)

    title_font = load_font(ImageFont, 68, bold=True)
    body_font = load_font(ImageFont, 40)
    footer_font = load_font(ImageFont, 28)
    label_font = load_font(ImageFont, 26, bold=True)

    margin_x = 96
    top_margin = 120
    bottom_margin = 120
    content_width = width - margin_x * 2

    draw.rounded_rectangle(
        [(margin_x - 28, top_margin - 28), (width - margin_x + 28, height - bottom_margin + 8)],
        radius=36,
        fill="#FFFFFF",
        outline=style["divider_color"],
        width=2,
    )

    draw.rounded_rectangle(
        [(margin_x, 72), (margin_x + 200, 112)],
        radius=20,
        fill=style["accent_color"],
    )
    
    draw.text((margin_x + 20, 79), "小红书", font=label_font, fill="#FFFFFF")

    title_lines = fit_lines(draw, title, title_font, content_width, max_lines=4, ellipsis=True)
    body_lines = fit_lines(draw, content, body_font, content_width, max_lines=18, ellipsis=True)
    footer_line = build_footer_text(footer_text)

    current_y = top_margin
    current_y = render_multiline(
        draw,
        title_lines,
        (margin_x, current_y),
        font=title_font,
        fill=style["title_color"],
        spacing=16,
    )

    current_y += 48
    draw.line(
        [(margin_x, current_y), (width - margin_x, current_y)],
        fill=style["divider_color"],
        width=3,
    )

    current_y += 52
    render_multiline(
        draw,
        body_lines,
        (margin_x, current_y),
        font=body_font,
        fill=style["body_color"],
        spacing=18,
    )

    footer_y = height - bottom_margin - 48
    draw.line(
        [(margin_x, footer_y - 24), (width - margin_x, footer_y - 24)],
        fill=style["divider_color"],
        width=2,
    )
    draw.text((margin_x, footer_y), footer_line, font=footer_font, fill=style["muted_color"])

    safe_slug = "-".join(textwrap.shorten(title or "poster", width=24, placeholder="").split()) or "poster"
    safe_slug = "".join(char if char.isalnum() or char in ("-", "_") else "-" for char in safe_slug).strip("-") or "poster"
    output_path = Path(tempfile.gettempdir()) / f"xhs-poster-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{safe_slug}.png"
    image.save(output_path, format="PNG")
    return str(output_path)


def enrich_publish_result(result, auto_generated, generated_image_path, images):
    if isinstance(result, dict):
        result.setdefault("_client", {})
        result["_client"].update(
            {
                "auto_generated_image": auto_generated,
                "generated_image_path": generated_image_path,
                "images_sent": images,
            }
        )
    return result


def main():
    global BASE_URL
    parser = argparse.ArgumentParser(description="Xiaohongshu MCP Client")
    parser.add_argument("--base-url", default="http://localhost:18060", help="Base URL of the MCP server")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("check_login_status", help="Check login status")
    subparsers.add_parser("get_login_qrcode", help="Get login QR code")
    subparsers.add_parser("delete_cookies", help="Delete cookies (reset login)")

    publish_help = "Publish an image note. Use --images for direct image posting, or omit it to auto-generate a text poster from title and content."
    p_publish = subparsers.add_parser(
        "publish_content",
        help=publish_help,
        description=(
            "Publish a Xiaohongshu image note. If --images is provided, the script uploads those images directly. "
            "If --images is omitted, the client auto-generates a local PNG text poster from --title and --content, "
            "then sends that generated image to /api/v1/publish."
        ),
        epilog=(
            "Examples:\n"
            "  python scripts/xhs_client.py publish_content --title \"今天的小总结\" --content \"记录一下今天做了什么\" --images C:/tmp/a.png\n"
            "  python scripts/xhs_client.py publish_content --title \"hello 测试一下\" --content \"朋友们好，这是 OpenClaw 发的测试帖。\"\n"
            "  python scripts/xhs_client.py publish_content --title-file title.txt --content-file content.txt --poster-style warm --poster-footer \"测试帖，请勿互动\""
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p_publish.add_argument("--title", help="Note title")
    p_publish.add_argument("--title-file", help="File containing note title")
    p_publish.add_argument("--content", help="Note content")
    p_publish.add_argument("--content-file", help="File containing note content")
    p_publish.add_argument("--images", nargs="+", help="Image paths or URLs. If omitted, a local text poster PNG is generated automatically.")
    p_publish.add_argument(
        "--poster-style",
        choices=sorted(POSTER_STYLES.keys()),
        default=DEFAULT_POSTER_STYLE,
        help="Poster style used only when --images is omitted",
    )
    p_publish.add_argument("--poster-footer", help="Optional footer text for the auto-generated poster")
    p_publish.add_argument("--tags", nargs="*", help="Tags")
    p_publish.add_argument("--schedule_at", help="Schedule time (ISO8601)")
    p_publish.add_argument("--is_original", action="store_true", help="Is original")
    p_publish.add_argument("--visibility", help="Visibility (公开可见, 仅自己可见, 仅互关好友可见)")
    p_publish.add_argument("--products", nargs="*", help="Products")

    p_video = subparsers.add_parser("publish_video", help="Publish video note")
    p_video.add_argument("--title", help="Video title")
    p_video.add_argument("--title-file", help="File containing video title")
    p_video.add_argument("--content", help="Video content")
    p_video.add_argument("--content-file", help="File containing video content")
    p_video.add_argument("--video", required=True, help="Local video path")
    p_video.add_argument("--tags", nargs="*", help="Tags")
    p_video.add_argument("--schedule_at", help="Schedule time (ISO8601)")
    p_video.add_argument("--visibility", help="Visibility")
    p_video.add_argument("--products", nargs="*", help="Products")

    subparsers.add_parser("list_feeds", help="List feeds")

    p_search = subparsers.add_parser("search_feeds", help="Search feeds")
    p_search.add_argument("--keyword", required=True, help="Search keyword")
    p_search.add_argument("--sort_by", help="Sort by (综合, 最新, 最多点赞, 最多评论, 最多收藏)")
    p_search.add_argument("--note_type", help="Note type (不限, 视频, 图文)")
    p_search.add_argument("--publish_time", help="Publish time (不限, 一天内, 一周内, 半年内)")
    p_search.add_argument("--search_scope", help="Search scope (不限, 已看过, 未看过, 已关注)")
    p_search.add_argument("--location", help="Location (不限, 同城, 附近)")

    p_detail = subparsers.add_parser("get_feed_detail", help="Get feed detail")
    p_detail.add_argument("--feed_id", required=True, help="Feed ID")
    p_detail.add_argument("--xsec_token", required=True, help="Xsec Token")
    p_detail.add_argument("--load_all_comments", action="store_true", help="Load all comments")
    p_detail.add_argument("--limit", type=int, help="Limit comments")
    p_detail.add_argument("--click_more_replies", action="store_true", help="Click more replies")
    p_detail.add_argument("--reply_limit", type=int, help="Reply limit")
    p_detail.add_argument("--scroll_speed", help="Scroll speed (slow, normal, fast)")

    p_profile = subparsers.add_parser("user_profile", help="Get user profile")
    p_profile.add_argument("--user_id", required=True, help="User ID")
    p_profile.add_argument("--xsec_token", required=True, help="Xsec Token")

    p_comment = subparsers.add_parser("post_comment_to_feed", help="Post comment")
    p_comment.add_argument("--feed_id", required=True, help="Feed ID")
    p_comment.add_argument("--xsec_token", required=True, help="Xsec Token")
    p_comment.add_argument("--content", required=True, help="Comment content")

    p_reply = subparsers.add_parser("reply_comment_in_feed", help="Reply comment")
    p_reply.add_argument("--feed_id", required=True, help="Feed ID")
    p_reply.add_argument("--xsec_token", required=True, help="Xsec Token")
    p_reply.add_argument("--comment_id", help="Target comment ID")
    p_reply.add_argument("--user_id", help="Target user ID")
    p_reply.add_argument("--content", required=True, help="Reply content")

    p_like = subparsers.add_parser("like_feed", help="Like or unlike feed")
    p_like.add_argument("--feed_id", required=True, help="Feed ID")
    p_like.add_argument("--xsec_token", required=True, help="Xsec Token")
    p_like.add_argument("--unlike", action="store_true", help="Unlike instead of like")

    p_fav = subparsers.add_parser("favorite_feed", help="Favorite or unfavorite feed")
    p_fav.add_argument("--feed_id", required=True, help="Feed ID")
    p_fav.add_argument("--xsec_token", required=True, help="Xsec Token")
    p_fav.add_argument("--unfavorite", action="store_true", help="Unfavorite instead of favorite")

    args = parser.parse_args()

    if args.base_url:
        BASE_URL = args.base_url.rstrip("/")

    if not args.command:
        parser.print_help()
        sys.exit(1)

    result = None

    if args.command == "check_login_status":
        result = make_request("GET", "/api/v1/login/status")
    elif args.command == "get_login_qrcode":
        result = make_request("GET", "/api/v1/login/qrcode")
    elif args.command == "delete_cookies":
        result = make_request("DELETE", "/api/v1/login/cookies")
    elif args.command == "publish_content":
        title = read_text_arg(args.title, args.title_file, "title")
        content = read_text_arg(args.content, args.content_file, "content")

        title = normalize_newlines(title)
        content = normalize_newlines(content)

        if not title or not content:
            exit_with_error(
                "Both title and content must be provided (directly or via file). "
                "When --images is omitted, the client uses title + content to auto-generate a text poster."
            )

        auto_generated = False
        generated_image_path = None
        images = list(args.images or [])

        if not images:
            generated_image_path = generate_text_poster(
                title=title,
                content=content,
                style_name=args.poster_style,
                footer_text=args.poster_footer,
            )
            images = [generated_image_path]
            auto_generated = True

        data = {
            "title": title,
            "content": content,
            "images": images,
        }
        if args.tags:
            data["tags"] = args.tags
        if args.schedule_at:
            data["schedule_at"] = args.schedule_at
        if args.is_original:
            data["is_original"] = args.is_original
        if args.visibility:
            data["visibility"] = args.visibility
        if args.products:
            data["products"] = args.products
        result = make_request("POST", "/api/v1/publish", data)
        result = enrich_publish_result(result, auto_generated, generated_image_path, images)
    elif args.command == "publish_video":
        title = read_text_arg(args.title, args.title_file, "title")
        content = read_text_arg(args.content, args.content_file, "content")

        title = normalize_newlines(title)
        content = normalize_newlines(content)

        if not title or not content:
            exit_with_error("Both title and content must be provided (either directly or via file).")

        data = {
            "title": title,
            "content": content,
            "video": args.video,
        }
        if args.tags:
            data["tags"] = args.tags
        if args.schedule_at:
            data["schedule_at"] = args.schedule_at
        if args.visibility:
            data["visibility"] = args.visibility
        if args.products:
            data["products"] = args.products
        result = make_request("POST", "/api/v1/publish_video", data)
    elif args.command == "list_feeds":
        result = make_request("GET", "/api/v1/feeds/list")
    elif args.command == "search_feeds":
        data = {"keyword": args.keyword, "filters": {}}
        if args.sort_by:
            data["filters"]["sort_by"] = args.sort_by
        if args.note_type:
            data["filters"]["note_type"] = args.note_type
        if args.publish_time:
            data["filters"]["publish_time"] = args.publish_time
        if args.search_scope:
            data["filters"]["search_scope"] = args.search_scope
        if args.location:
            data["filters"]["location"] = args.location
        result = make_request("POST", "/api/v1/feeds/search", data)
    elif args.command == "get_feed_detail":
        data = {
            "feed_id": args.feed_id,
            "xsec_token": args.xsec_token,
            "load_all_comments": args.load_all_comments,
        }
        if args.load_all_comments:
            config = {}
            if args.click_more_replies:
                config["click_more_replies"] = args.click_more_replies
            if args.limit is not None:
                config["max_comment_items"] = args.limit
            if args.reply_limit is not None:
                config["max_replies_threshold"] = args.reply_limit
            if args.scroll_speed:
                config["scroll_speed"] = args.scroll_speed
            if config:
                data["comment_config"] = config
        result = make_request("POST", "/api/v1/feeds/detail", data)
    elif args.command == "user_profile":
        data = {
            "user_id": args.user_id,
            "xsec_token": args.xsec_token,
        }
        result = make_request("POST", "/api/v1/user/profile", data)
    elif args.command == "post_comment_to_feed":
        data = {
            "feed_id": args.feed_id,
            "xsec_token": args.xsec_token,
            "content": args.content,
        }
        result = make_request("POST", "/api/v1/feeds/comment", data)
    elif args.command == "reply_comment_in_feed":
        data = {
            "feed_id": args.feed_id,
            "xsec_token": args.xsec_token,
            "content": args.content,
        }
        if args.comment_id:
            data["comment_id"] = args.comment_id
        if args.user_id:
            data["user_id"] = args.user_id
        result = make_request("POST", "/api/v1/feeds/comment/reply", data)
    elif args.command == "like_feed":
        arguments = {
            "feed_id": args.feed_id,
            "xsec_token": args.xsec_token,
        }
        if args.unlike:
            arguments["unlike"] = args.unlike
        result = call_mcp_tool("like_feed", arguments)
    elif args.command == "favorite_feed":
        arguments = {
            "feed_id": args.feed_id,
            "xsec_token": args.xsec_token,
        }
        if args.unfavorite:
            arguments["unfavorite"] = args.unfavorite
        result = call_mcp_tool("favorite_feed", arguments)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
