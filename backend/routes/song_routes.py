from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse, Response
import subprocess
import asyncio
import os
import json
import sys
import shutil
import requests as req_lib
from concurrent.futures import ThreadPoolExecutor

router = APIRouter(prefix="/songs", tags=["Songs"])

# ── Binary detection ──────────────────────────────────────────────────────────
_win_binary = os.path.join(os.path.dirname(__file__), "..", "yt-dlp.exe")
if sys.platform == "win32" and os.path.exists(_win_binary):
    YT_DLP = _win_binary
else:
    YT_DLP = shutil.which("yt-dlp") or "yt-dlp"

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "audio_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

_executor = ThreadPoolExecutor(max_workers=4)

# ── Common yt-dlp flags that bypass bot-detection ─────────────────────────────
# Using the "android" or "mweb" client sidesteps the sign-in challenge.
# Also force IPv4 to avoid Render's IPv6 issues.
BYPASS_ARGS = [
    "--extractor-args", "youtube:player_client=android,web",
    "--force-ipv4",
    "--no-playlist",
    "--no-warnings",
    "--no-check-certificates",
]

# YouTube has started blocking Render's (and most cloud) IPs outright with
# "Sign in to confirm you're not a bot" — the android/web client spoofing
# above is no longer enough on its own. The only reliable workaround left is
# supplying cookies from a real, logged-in YouTube session. If a cookies
# file is present (see YT_COOKIES_PATH / README for how to generate one),
# pass it to yt-dlp so it authenticates as a real browser session instead
# of an anonymous datacenter request.
YT_COOKIES_PATH = os.environ.get(
    "YT_COOKIES_PATH",
    os.path.join(os.path.dirname(__file__), "..", "cookies.txt"),
)
if os.path.exists(YT_COOKIES_PATH):
    BYPASS_ARGS += ["--cookies", YT_COOKIES_PATH]
    print(f"[INFO] Using YouTube cookies from {YT_COOKIES_PATH}")
else:
    print(
        f"[WARN] No YouTube cookies file found at {YT_COOKIES_PATH} — "
        "search may work but stream/download will likely fail with "
        "'Sign in to confirm you're not a bot' since Render's IP is "
        "flagged. See README for how to generate cookies.txt."
    )


# ── Search ─────────────────────────────────────────────────────────────────────
def _run_search(q: str):
    """Search YouTube using yt-dlp Python API (no subprocess crash on Py3.14)."""
    import yt_dlp

    results = []
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'force_ipv4': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch5:{q}", download=False)
            entries = info.get('entries', []) if info else []
            for item in entries:
                if not item:
                    continue
                vid_id = item.get('id') or item.get('url', '').split('v=')[-1]
                results.append({
                    'id': vid_id,
                    'title': item.get('title', 'Unknown'),
                    'artist': item.get('uploader') or item.get('channel') or 'Unknown Artist',
                    'thumbnail': f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg",
                    'duration': item.get('duration'),
                })
    except Exception as e:
        raise RuntimeError(f"yt-dlp Python API search failed: {e}")

    return results


def _run_search_fallback(q: str):
    """Fallback search using innertube (YouTube internal API, no yt-dlp needed)."""
    import innertube
    client = innertube.InnerTube("WEB")
    data = client.search(q)

    # Parse the nested YouTube response structure
    out = []
    try:
        section = (
            data.get("contents", {})
            .get("twoColumnSearchResultsRenderer", {})
            .get("primaryContents", {})
            .get("sectionListRenderer", {})
            .get("contents", [{}])[0]
            .get("itemSectionRenderer", {})
            .get("contents", [])
        )
        for item in section:
            vr = item.get("videoRenderer", {})
            vid_id = vr.get("videoId", "")
            if not vid_id:
                continue
            title = (vr.get("title", {}).get("runs") or [{}])[0].get("text", "Unknown")
            artist = (
                vr.get("ownerText", {}).get("runs") or
                vr.get("longBylineText", {}).get("runs") or
                [{}]
            )[0].get("text", "Unknown Artist")
            # Duration from "lengthText"
            dur_text = (vr.get("lengthText") or {}).get("simpleText", "") or ""
            parts = dur_text.split(":")
            try:
                secs = int(parts[-1]) + int(parts[-2]) * 60 if len(parts) >= 2 else int(parts[0])
            except Exception:
                secs = None
            out.append({
                "id": vid_id,
                "title": title,
                "artist": artist,
                "thumbnail": f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg",
                "duration": secs,
            })
            if len(out) >= 5:
                break
    except Exception as e:
        raise RuntimeError(f"innertube search parse failed: {e}")

    return out


@router.get("/search")
async def search_songs(q: str = Query(..., min_length=1)):
    """Search YouTube for songs. Returns up to 5 results."""
    try:
        loop = asyncio.get_event_loop()
        try:
            results = await loop.run_in_executor(_executor, _run_search, q)
            if results:
                return results
            raise RuntimeError("Empty results from yt-dlp")
        except Exception as e1:
            print(f"[WARN] yt-dlp search failed: {e1}. Trying youtube-search-python...")
            results = await loop.run_in_executor(_executor, _run_search_fallback, q)
            return results
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Search timed out")
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ── Stream URL resolution (no download to disk) ───────────────────────────────
def _get_stream_url(video_id: str) -> str:
    """
    Resolve a direct audio stream URL using yt-dlp with Android client bypass.
    Returns the URL string on success, raises RuntimeError on failure.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    proc = subprocess.run(
        [
            YT_DLP,
            "-f", "bestaudio[ext=m4a]/bestaudio/best",
            "--get-url",
            url,
        ] + BYPASS_ARGS,
        capture_output=True,
        text=True,
        timeout=30,
    )
    # Check stdout for a valid URL — returncode may be 1 due to cookie-save
    # failures on read-only filesystems (Render), even if URL extraction succeeded.
    stream_url = proc.stdout.strip().split("\n")[0].strip()
    if stream_url and stream_url.startswith("http"):
        return stream_url
    raise RuntimeError(
        f"yt-dlp URL extraction failed (rc={proc.returncode}): {proc.stderr[:400]}"
    )


def _get_stream_url_pytubefix(video_id: str) -> str:
    """Fallback: use pytubefix to get a direct stream URL."""
    try:
        from pytubefix import YouTube
        from pytubefix.cli import on_progress
        yt = YouTube(
            f"https://www.youtube.com/watch?v={video_id}",
            use_oauth=False,
            allow_oauth_cache=False,
        )
        stream = yt.streams.filter(only_audio=True, file_extension="mp4").first()
        if not stream:
            stream = yt.streams.filter(only_audio=True).first()
        if not stream:
            raise RuntimeError("No audio stream found via pytubefix")
        return stream.url
    except Exception as e:
        raise RuntimeError(f"pytubefix failed: {e}")


def _resolve_stream_url(video_id: str) -> str:
    """Try yt-dlp first, fall back to pytubefix."""
    try:
        return _get_stream_url(video_id)
    except Exception as e1:
        print(f"[WARN] yt-dlp stream resolution failed: {e1}. Trying pytubefix...")
        try:
            return _get_stream_url_pytubefix(video_id)
        except Exception as e2:
            raise RuntimeError(f"All stream resolvers failed. yt-dlp: {e1} | pytubefix: {e2}")


# ── Proxy-stream endpoint ─────────────────────────────────────────────────────
@router.get("/stream/{video_id}")
async def stream_song(video_id: str, request: Request):
    """
    Resolve a direct audio URL and proxy it to the client.
    This avoids downloading to disk and streams directly.
    """
    if video_id.endswith(".m4a"):
        video_id = video_id[:-4]

    # 1. Check disk cache first (fast path)
    cache_path = os.path.join(CACHE_DIR, f"{video_id}.m4a")
    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 10_000:
        file_size = os.path.getsize(cache_path)

        # Handle Range requests for seekable audio
        range_header = request.headers.get("range")
        if range_header:
            start, end = _parse_range(range_header, file_size)
            length = end - start + 1

            def ranged_iter():
                with open(cache_path, "rb") as f:
                    f.seek(start)
                    remaining = length
                    while remaining > 0:
                        chunk = f.read(min(65536, remaining))
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk

            return StreamingResponse(
                ranged_iter(),
                status_code=206,
                media_type="audio/mp4",
                headers={
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Content-Length": str(length),
                    "Accept-Ranges": "bytes",
                },
            )

        def file_iter():
            with open(cache_path, "rb") as f:
                while chunk := f.read(65536):
                    yield chunk

        return StreamingResponse(
            file_iter(),
            media_type="audio/mp4",
            headers={
                "Content-Length": str(file_size),
                "Accept-Ranges": "bytes",
            },
        )

    # 2. Resolve stream URL
    try:
        loop = asyncio.get_event_loop()
        stream_url = await loop.run_in_executor(_executor, _resolve_stream_url, video_id)
    except Exception as e:
        print(f"[ERROR] Could not resolve stream for {video_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Could not resolve stream: {e}")

    # 3. Proxy the stream from Google's servers to the client
    #    Forward Range header if present so seeking works
    range_header = request.headers.get("range")
    upstream_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 11; Pixel 5) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/90.0.4430.91 Mobile Safari/537.36"
        ),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }
    if range_header:
        upstream_headers["Range"] = range_header

    try:
        upstream = req_lib.get(stream_url, headers=upstream_headers, stream=True, timeout=30)
        upstream.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Upstream fetch failed for {video_id}: {e}")
        raise HTTPException(status_code=502, detail=f"Upstream audio fetch failed: {e}")

    status_code = upstream.status_code  # 200 or 206
    # Force audio/mp4 — Google returns "video/mp4" which browsers refuse to
    # play inside an <audio> element. The data is audio-only either way.
    resp_headers = {
        "Accept-Ranges": "bytes",
        "Cache-Control": "no-cache",
        "Content-Type": "audio/mp4",
    }
    if "Content-Length" in upstream.headers:
        resp_headers["Content-Length"] = upstream.headers["Content-Length"]
    if "Content-Range" in upstream.headers:
        resp_headers["Content-Range"] = upstream.headers["Content-Range"]

    def upstream_iter():
        for chunk in upstream.iter_content(chunk_size=65536):
            if chunk:
                yield chunk

    return StreamingResponse(
        upstream_iter(),
        status_code=status_code,
        media_type="audio/mp4",
        headers=resp_headers,
    )


def _parse_range(range_header: str, file_size: int):
    """Parse HTTP Range header. Returns (start, end) inclusive."""
    try:
        unit, ranges = range_header.split("=")
        start_str, end_str = ranges.split("-")
        start = int(start_str) if start_str else 0
        end = int(end_str) if end_str else file_size - 1
        end = min(end, file_size - 1)
        return start, end
    except Exception:
        return 0, file_size - 1


# ── Debug endpoint ─────────────────────────────────────────────────────────────
@router.get("/debug_dl/{video_id}")
async def debug_dl(video_id: str):
    """Debug endpoint: test yt-dlp URL extraction and return raw output."""
    if video_id.endswith(".m4a"):
        video_id = video_id[:-4]
    url = f"https://www.youtube.com/watch?v={video_id}"
    proc = subprocess.run(
        [YT_DLP, "-f", "bestaudio[ext=m4a]/bestaudio/best", "--get-url", url] + BYPASS_ARGS,
        capture_output=True,
        text=True,
        timeout=60,
    )
    stream_url = proc.stdout.strip().split("\n")[0] if proc.stdout.strip() else None

    # Also try pytubefix
    pytubefix_url = None
    pytubefix_error = None
    try:
        pytubefix_url = _get_stream_url_pytubefix(video_id)
    except Exception as e:
        pytubefix_error = str(e)

    return {
        "video_id": video_id,
        "yt_dlp_returncode": proc.returncode,
        "yt_dlp_stream_url": stream_url,
        "yt_dlp_stderr": proc.stderr[:1000],
        "pytubefix_stream_url": pytubefix_url,
        "pytubefix_error": pytubefix_error,
    }


# ── Lyrics placeholder ─────────────────────────────────────────────────────────
@router.get("/lyrics/{video_id}")
async def get_lyrics(video_id: str):
    """Placeholder for lyrics fetching."""
    return {"lyrics": "Lyrics feature coming soon!"}
