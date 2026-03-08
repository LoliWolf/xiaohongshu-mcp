import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

API_URL = "https://cn.bing.com/HPImageArchive.aspx"
BING_BASE_URL = "https://cn.bing.com"
DEFAULT_TIMEOUT = 30
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


def build_api_url():
    return f"{API_URL}?format=js&idx=0&n=1&mkt=zh-CN"


def ensure_output_dir(output_dir: str) -> Path:
    path = Path(output_dir).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def fetch_metadata(session: requests.Session) -> dict:
    response = session.get(build_api_url(), timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    payload = response.json()

    images = payload.get("images") or []
    if not images:
        raise ValueError("Bing API 返回中未包含 images 数据")

    return images[0]


def build_image_url(image_info: dict) -> str:
    url = image_info.get("url")
    if not url:
        raise ValueError("Bing API 返回中缺少图片 url 字段")
    return urljoin(BING_BASE_URL, url)


def detect_extension(image_url: str, content_type: str) -> str:
    parsed = urlparse(image_url)
    suffix = Path(parsed.path).suffix
    if suffix:
        return suffix

    mapping = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }
    for key, value in mapping.items():
        if key in (content_type or ""):
            return value
    return ".jpg"


def download_image(session: requests.Session, image_url: str, output_dir: Path, startdate: str) -> Path:
    response = session.get(image_url, timeout=DEFAULT_TIMEOUT, stream=True)
    response.raise_for_status()

    extension = detect_extension(image_url, response.headers.get("Content-Type", ""))
    file_path = output_dir / f"bing_wallpaper_{startdate}{extension}"

    with open(file_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)

    return file_path


def main():
    parser = argparse.ArgumentParser(description="下载 Bing 每日壁纸并输出版权信息")
    parser.add_argument("output_dir", help="图片保存目录")
    args = parser.parse_args()

    output_dir = ensure_output_dir(args.output_dir)

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    try:
        image_info = fetch_metadata(session)
        image_url = build_image_url(image_info)
        startdate = image_info.get("startdate") or "unknown"
        saved_path = download_image(session, image_url, output_dir, startdate)
    except requests.RequestException as exc:
        print(f"Error: 请求 Bing 壁纸接口或图片失败: {exc}", file=sys.stderr)
        sys.exit(1)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    result = {
        "copyright": image_info.get("copyright", ""),
        "copyright_link": image_info.get("copyrightlink", ""),
        "title": image_info.get("title", ""),
        "startdate": startdate,
        "image_url": image_url,
        "saved_path": str(saved_path),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
