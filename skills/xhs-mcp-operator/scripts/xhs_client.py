import argparse
import json
import urllib.request
import urllib.error
import sys

BASE_URL = "http://localhost:18060"

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
    # The MCP server is available at /mcp
    # We can send a JSON-RPC request to call a tool
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "id": 1
    }
    return make_request("POST", "/mcp", payload)

def main():
    global BASE_URL
    parser = argparse.ArgumentParser(description="Xiaohongshu MCP Client")
    parser.add_argument("--base-url", default="http://localhost:18060", help="Base URL of the MCP server")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 1. check_login_status
    subparsers.add_parser("check_login_status", help="Check login status")

    # 2. get_login_qrcode
    subparsers.add_parser("get_login_qrcode", help="Get login QR code")

    # 3. delete_cookies
    subparsers.add_parser("delete_cookies", help="Delete cookies (reset login)")

    # 4. publish_content
    p_publish = subparsers.add_parser("publish_content", help="Publish image note")
    p_publish.add_argument("--title", help="Note title")
    p_publish.add_argument("--title-file", help="File containing note title")
    p_publish.add_argument("--content", help="Note content")
    p_publish.add_argument("--content-file", help="File containing note content")
    p_publish.add_argument("--images", required=True, nargs="+", help="Image paths or URLs")
    p_publish.add_argument("--tags", nargs="*", help="Tags")
    p_publish.add_argument("--schedule_at", help="Schedule time (ISO8601)")
    p_publish.add_argument("--is_original", action="store_true", help="Is original")
    p_publish.add_argument("--visibility", help="Visibility (公开可见, 仅自己可见, 仅互关好友可见)")
    p_publish.add_argument("--products", nargs="*", help="Products")

    # 5. publish_video
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

    # 6. list_feeds
    subparsers.add_parser("list_feeds", help="List feeds")

    # 7. search_feeds
    p_search = subparsers.add_parser("search_feeds", help="Search feeds")
    p_search.add_argument("--keyword", required=True, help="Search keyword")
    p_search.add_argument("--sort_by", help="Sort by (综合, 最新, 最多点赞, 最多评论, 最多收藏)")
    p_search.add_argument("--note_type", help="Note type (不限, 视频, 图文)")
    p_search.add_argument("--publish_time", help="Publish time (不限, 一天内, 一周内, 半年内)")
    p_search.add_argument("--search_scope", help="Search scope (不限, 已看过, 未看过, 已关注)")
    p_search.add_argument("--location", help="Location (不限, 同城, 附近)")

    # 8. get_feed_detail
    p_detail = subparsers.add_parser("get_feed_detail", help="Get feed detail")
    p_detail.add_argument("--feed_id", required=True, help="Feed ID")
    p_detail.add_argument("--xsec_token", required=True, help="Xsec Token")
    p_detail.add_argument("--load_all_comments", action="store_true", help="Load all comments")
    p_detail.add_argument("--limit", type=int, help="Limit comments")
    p_detail.add_argument("--click_more_replies", action="store_true", help="Click more replies")
    p_detail.add_argument("--reply_limit", type=int, help="Reply limit")
    p_detail.add_argument("--scroll_speed", help="Scroll speed (slow, normal, fast)")

    # 9. user_profile
    p_profile = subparsers.add_parser("user_profile", help="Get user profile")
    p_profile.add_argument("--user_id", required=True, help="User ID")
    p_profile.add_argument("--xsec_token", required=True, help="Xsec Token")

    # 10. post_comment_to_feed
    p_comment = subparsers.add_parser("post_comment_to_feed", help="Post comment")
    p_comment.add_argument("--feed_id", required=True, help="Feed ID")
    p_comment.add_argument("--xsec_token", required=True, help="Xsec Token")
    p_comment.add_argument("--content", required=True, help="Comment content")

    # 11. reply_comment_in_feed
    p_reply = subparsers.add_parser("reply_comment_in_feed", help="Reply comment")
    p_reply.add_argument("--feed_id", required=True, help="Feed ID")
    p_reply.add_argument("--xsec_token", required=True, help="Xsec Token")
    p_reply.add_argument("--comment_id", help="Target comment ID")
    p_reply.add_argument("--user_id", help="Target user ID")
    p_reply.add_argument("--content", required=True, help="Reply content")

    # 12. like_feed
    p_like = subparsers.add_parser("like_feed", help="Like or unlike feed")
    p_like.add_argument("--feed_id", required=True, help="Feed ID")
    p_like.add_argument("--xsec_token", required=True, help="Xsec Token")
    p_like.add_argument("--unlike", action="store_true", help="Unlike instead of like")

    # 13. favorite_feed
    p_fav = subparsers.add_parser("favorite_feed", help="Favorite or unfavorite feed")
    p_fav.add_argument("--feed_id", required=True, help="Feed ID")
    p_fav.add_argument("--xsec_token", required=True, help="Xsec Token")
    p_fav.add_argument("--unfavorite", action="store_true", help="Unfavorite instead of favorite")

    args = parser.parse_args()

    if args.base_url:
        BASE_URL = args.base_url.rstrip('/')

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
        title = args.title
        if args.title_file:
            with open(args.title_file, 'r', encoding='utf-8') as f:
                title = f.read().strip()
        
        content = args.content
        if args.content_file:
            with open(args.content_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()

        if not title or not content:
            print("Error: Both title and content must be provided (either directly or via file).")
            sys.exit(1)

        data = {
            "title": title,
            "content": content,
            "images": args.images,
        }
        if args.tags: data["tags"] = args.tags
        if args.schedule_at: data["schedule_at"] = args.schedule_at
        if args.is_original: data["is_original"] = args.is_original
        if args.visibility: data["visibility"] = args.visibility
        if args.products: data["products"] = args.products
        result = make_request("POST", "/api/v1/publish", data)
    elif args.command == "publish_video":
        title = args.title
        if args.title_file:
            with open(args.title_file, 'r', encoding='utf-8') as f:
                title = f.read().strip()
        
        content = args.content
        if args.content_file:
            with open(args.content_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()

        if not title or not content:
            print("Error: Both title and content must be provided (either directly or via file).")
            sys.exit(1)

        data = {
            "title": title,
            "content": content,
            "video": args.video,
        }
        if args.tags: data["tags"] = args.tags
        if args.schedule_at: data["schedule_at"] = args.schedule_at
        if args.visibility: data["visibility"] = args.visibility
        if args.products: data["products"] = args.products
        result = make_request("POST", "/api/v1/publish_video", data)
    elif args.command == "list_feeds":
        result = make_request("GET", "/api/v1/feeds/list")
    elif args.command == "search_feeds":
        data = {"keyword": args.keyword, "filters": {}}
        if args.sort_by: data["filters"]["sort_by"] = args.sort_by
        if args.note_type: data["filters"]["note_type"] = args.note_type
        if args.publish_time: data["filters"]["publish_time"] = args.publish_time
        if args.search_scope: data["filters"]["search_scope"] = args.search_scope
        if args.location: data["filters"]["location"] = args.location
        result = make_request("POST", "/api/v1/feeds/search", data)
    elif args.command == "get_feed_detail":
        data = {
            "feed_id": args.feed_id,
            "xsec_token": args.xsec_token,
            "load_all_comments": args.load_all_comments,
        }
        if args.load_all_comments:
            config = {}
            if args.click_more_replies: config["click_more_replies"] = args.click_more_replies
            if args.limit is not None: config["max_comment_items"] = args.limit
            if args.reply_limit is not None: config["max_replies_threshold"] = args.reply_limit
            if args.scroll_speed: config["scroll_speed"] = args.scroll_speed
            if config: data["comment_config"] = config
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
        if args.comment_id: data["comment_id"] = args.comment_id
        if args.user_id: data["user_id"] = args.user_id
        result = make_request("POST", "/api/v1/feeds/comment/reply", data)
    elif args.command == "like_feed":
        # like_feed is not in HTTP API, use MCP tool call
        arguments = {
            "feed_id": args.feed_id,
            "xsec_token": args.xsec_token,
        }
        if args.unlike: arguments["unlike"] = args.unlike
        result = call_mcp_tool("like_feed", arguments)
    elif args.command == "favorite_feed":
        # favorite_feed is not in HTTP API, use MCP tool call
        arguments = {
            "feed_id": args.feed_id,
            "xsec_token": args.xsec_token,
        }
        if args.unfavorite: arguments["unfavorite"] = args.unfavorite
        result = call_mcp_tool("favorite_feed", arguments)

    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
