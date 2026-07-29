from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import subprocess
import asyncio
import os
import json
from concurrent.futures import ThreadPoolExecutor

router = APIRouter(prefix="/songs", tags=["Songs"])

import sys
import shutil

# Detect yt-dlp binary: use .exe on Windows, system command on Linux (Render)
_win_binary = os.path.join(os.path.dirname(__file__), "..", "yt-dlp.exe")
if sys.platform == "win32" and os.path.exists(_win_binary):
    YT_DLP = _win_binary
else:
    # On Linux (Render.com), yt-dlp is installed via pip
    YT_DLP = shutil.which("yt-dlp") or "yt-dlp"

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "audio_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# Thread pool for blocking subprocess calls (Windows asyncio subprocess workaround)
_executor = ThreadPoolExecutor(max_workers=4)


def _run_search(q: str):
    """Blocking search using subprocess (runs in thread pool)."""
    proc = subprocess.run(
        [YT_DLP, f"ytsearch5:{q}", "--dump-json", "--no-playlist", "--flat-playlist", "--no-warnings"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {proc.stderr[:200]}")
    
    results = []
    for line in proc.stdout.strip().split("\n"):
        if not line.strip():
            continue
        item = json.loads(line)
        results.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "artist": item.get("uploader") or item.get("channel") or "Unknown Artist",
            "thumbnail": f"https://i.ytimg.com/vi/{item.get('id')}/hqdefault.jpg",
            "duration": item.get("duration"),
        })
    return results


def _run_download(video_id: str, cache_path: str):
    """Blocking download using subprocess (runs in thread pool)."""
    proc = subprocess.run(
        [
            YT_DLP,
            "-f", "bestaudio[ext=m4a]/bestaudio/best",
            "-o", cache_path,
            "--no-playlist", "--no-warnings",
            f"https://www.youtube.com/watch?v={video_id}",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return proc.returncode


@router.get("/search")
async def search_songs(q: str = Query(..., min_length=1)):
    """Search YouTube for songs. Returns up to 5 results."""
    try:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(_executor, _run_search, q)
        return results
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Search timed out")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stream/{video_id}")
async def stream_song(video_id: str):
    """
    Stream audio for a given YouTube video ID.
    Downloads to cache on first request, then serves from cache.
    """
    # Strip .m4a extension if present
    if video_id.endswith(".m4a"):
        video_id = video_id[:-4]

    cache_path = os.path.join(CACHE_DIR, f"{video_id}.m4a")

    # Download if not cached
    if not os.path.exists(cache_path):
        loop = asyncio.get_event_loop()
        returncode = await loop.run_in_executor(_executor, _run_download, video_id, cache_path)

        if not os.path.exists(cache_path):
            raise HTTPException(status_code=500, detail="Failed to download audio")

    file_size = os.path.getsize(cache_path)

    def file_iterator():
        with open(cache_path, "rb") as f:
            while chunk := f.read(65536):
                yield chunk

    return StreamingResponse(
        file_iterator(),
        media_type="audio/mp4",
        headers={
            "Content-Length": str(file_size),
            "Accept-Ranges": "bytes",
            "Content-Disposition": f'inline; filename="{video_id}.m4a"',
        },
    )


@router.get("/lyrics/{video_id}")
async def get_lyrics(video_id: str):
    """Placeholder for lyrics fetching."""
    return {"lyrics": "Lyrics feature coming soon!"}
