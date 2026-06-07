from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


BASE_URL = "https://www.googleapis.com/youtube/v3"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


class YouTubeAPIError(RuntimeError):
    pass


def utc_now_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def ensure_directories() -> None:
    for folder in [
        RAW_DIR / "channels",
        RAW_DIR / "playlist_items",
        RAW_DIR / "videos",
        RAW_DIR / "comments",
    ]:
        folder.mkdir(parents=True, exist_ok=True)


def load_config() -> dict[str, Any]:
    load_dotenv(PROJECT_ROOT / ".env")

    api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY is required in .env")

    return {
        "api_key": api_key,
        "channel_handle": os.getenv("YOUTUBE_CHANNEL_HANDLE", "").strip().lstrip("@"),
        "channel_id": os.getenv("YOUTUBE_CHANNEL_ID", "").strip(),
        "uploads_playlist_id": os.getenv("YOUTUBE_UPLOADS_PLAYLIST_ID", "").strip(),
        "test_video_id": os.getenv("TEST_VIDEO_ID", "").strip(),
        "start_comment_page_token": os.getenv("START_COMMENT_PAGE_TOKEN", "").strip(),
        "max_playlist_items": int(os.getenv("MAX_PLAYLIST_ITEMS", "10")),
        "max_comment_videos": int(os.getenv("MAX_COMMENT_VIDEOS", "3")),
        "max_comments_per_video": int(os.getenv("MAX_COMMENTS_PER_VIDEO", "20")),
    }


def youtube_get(endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=30)
    if not response.ok:
        raise YouTubeAPIError(
            f"Request failed for {endpoint}: {response.status_code} {response.text}"
        )
    return response.json()


def save_json(payload: dict[str, Any], output_path: Path) -> None:
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def fetch_channel(config: dict[str, Any]) -> dict[str, Any]:
    params: dict[str, Any] = {
        "part": "snippet,statistics,contentDetails",
        "key": config["api_key"],
    }
    if config["channel_id"]:
        params["id"] = config["channel_id"]
    elif config["channel_handle"]:
        params["forHandle"] = config["channel_handle"]
    else:
        raise ValueError("Either YOUTUBE_CHANNEL_ID or YOUTUBE_CHANNEL_HANDLE must be set")

    payload = youtube_get("channels", params)
    items = payload.get("items", [])
    if not items:
        raise YouTubeAPIError("No channel found from channels.list response")
    return payload


def extract_channel_metadata(channel_payload: dict[str, Any]) -> dict[str, str]:
    item = channel_payload["items"][0]
    uploads_playlist_id = item["contentDetails"]["relatedPlaylists"]["uploads"]
    return {
        "channel_id": item["id"],
        "channel_title": item["snippet"]["title"],
        "uploads_playlist_id": uploads_playlist_id,
    }


def fetch_playlist_items(config: dict[str, Any], uploads_playlist_id: str) -> dict[str, Any]:
    params = {
        "part": "snippet,contentDetails",
        "playlistId": uploads_playlist_id,
        "maxResults": min(config["max_playlist_items"], 50),
        "key": config["api_key"],
    }
    return youtube_get("playlistItems", params)


def extract_video_ids(playlist_payload: dict[str, Any]) -> list[str]:
    video_ids: list[str] = []
    for item in playlist_payload.get("items", []):
        video_id = item.get("contentDetails", {}).get("videoId")
        if video_id:
            video_ids.append(video_id)
    return video_ids


def fetch_videos(config: dict[str, Any], video_ids: list[str]) -> dict[str, Any]:
    if not video_ids:
        return {"items": []}

    params = {
        "part": "snippet,statistics,contentDetails",
        "id": ",".join(video_ids),
        "key": config["api_key"],
    }
    return youtube_get("videos", params)


def fetch_comments_for_video(
    config: dict[str, Any], video_id: str, max_comments: int, start_page_token: str = ""
) -> dict[str, Any]:
    page_size = 100 if max_comments <= 0 else min(max_comments, 100)
    all_items: list[dict[str, Any]] = []
    next_page_token: str | None = start_page_token or None
    pages_fetched = 0
    started_from_page_token = bool(start_page_token)

    while True:
        params: dict[str, Any] = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": page_size,
            "key": config["api_key"],
        }
        if next_page_token:
            params["pageToken"] = next_page_token

        payload = youtube_get("commentThreads", params)
        items = payload.get("items", [])
        all_items.extend(items)
        pages_fetched += 1

        if max_comments > 0 and len(all_items) >= max_comments:
            all_items = all_items[:max_comments]
            next_page_token = payload.get("nextPageToken")
            break

        next_page_token = payload.get("nextPageToken")
        if not next_page_token:
            break

    return {
        "kind": "youtube#commentThreadListResponse",
        "videoId": video_id,
        "items": all_items,
        "pageInfo": {
            "totalResultsLoaded": len(all_items),
            "pagesFetched": pages_fetched,
            "startedFromPageToken": started_from_page_token,
        },
        "nextPageToken": next_page_token,
        "startPageToken": start_page_token or None,
    }


def build_manifest(
    channel_meta: dict[str, str],
    playlist_payload: dict[str, Any],
    videos_payload: dict[str, Any],
    comment_payloads: dict[str, dict[str, Any]],
    selected_video_ids: list[str],
) -> dict[str, Any]:
    return {
        "extracted_at": utc_now_slug(),
        "channel_id": channel_meta["channel_id"],
        "channel_title": channel_meta["channel_title"],
        "uploads_playlist_id": channel_meta["uploads_playlist_id"],
        "playlist_items_count": len(playlist_payload.get("items", [])),
        "videos_count": len(videos_payload.get("items", [])),
        "selected_video_ids": selected_video_ids,
        "comment_video_count": len(comment_payloads),
        "comment_counts": {
            video_id: len(payload.get("items", []))
            for video_id, payload in comment_payloads.items()
        },
        "comment_pages_fetched": {
            video_id: payload.get("pageInfo", {}).get("pagesFetched", 0)
            for video_id, payload in comment_payloads.items()
        },
        "comment_next_page_tokens": {
            video_id: payload.get("nextPageToken")
            for video_id, payload in comment_payloads.items()
        },
    }


def main() -> None:
    ensure_directories()
    config = load_config()
    run_slug = utc_now_slug()

    channel_payload = fetch_channel(config)
    channel_meta = extract_channel_metadata(channel_payload)

    playlist_payload = fetch_playlist_items(config, channel_meta["uploads_playlist_id"])
    video_ids = extract_video_ids(playlist_payload)
    videos_payload = fetch_videos(config, video_ids)

    if config["test_video_id"]:
        selected_video_ids = [config["test_video_id"]]
    else:
        selected_video_ids = video_ids[: config["max_comment_videos"]]

    comment_payloads: dict[str, dict[str, Any]] = {}
    for video_id in selected_video_ids:
        comment_payloads[video_id] = fetch_comments_for_video(
            config,
            video_id,
            config["max_comments_per_video"],
            config["start_comment_page_token"],
        )

    save_json(
        channel_payload,
        RAW_DIR / "channels" / f"{channel_meta['channel_id']}_{run_slug}.json",
    )
    save_json(
        playlist_payload,
        RAW_DIR / "playlist_items" / f"{channel_meta['uploads_playlist_id']}_{run_slug}.json",
    )
    save_json(
        videos_payload,
        RAW_DIR / "videos" / f"{channel_meta['channel_id']}_{run_slug}.json",
    )

    for video_id, payload in comment_payloads.items():
        save_json(payload, RAW_DIR / "comments" / f"{video_id}_{run_slug}.json")

    manifest = build_manifest(
        channel_meta,
        playlist_payload,
        videos_payload,
        comment_payloads,
        selected_video_ids,
    )
    save_json(manifest, RAW_DIR / f"manifest_{run_slug}.json")

    print("Extraction completed.")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
