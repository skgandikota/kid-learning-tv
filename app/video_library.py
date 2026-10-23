"""Confined local videos and one background YouTube download at a time.

Only immediate, non-symlink MP4/WebM/M4V files are indexed. Download jobs are
persisted; jobs active when a new library instance starts become failed with an
explicit interruption error. Use one library instance per application process.
FFmpeg/ffprobe must be on PATH; neither tool nor yt-dlp is needed at startup.
Downloads are capped at 2 GiB cumulatively and stop below 256 MiB free space.
Merging can temporarily require a second copy of the downloaded streams.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
from urllib.parse import parse_qs, urlsplit
import uuid


_LOG = logging.getLogger(__name__)
_EXTENSIONS = {".mp4", ".webm", ".m4v"}
_VIDEO_CODECS = {"h264", "vp8", "vp9", "av1"}
_AUDIO_CODECS = {"aac", "opus", "vorbis", "mp3"}
_ACTIVE = {"queued", "downloading", "processing"}
_JOB_LIMIT = 20
_MAX_DOWNLOAD_BYTES = 2 * 1024**3
_FREE_SPACE_RESERVE = 256 * 1024**2


class VideoLibrary:
    """Store videos in ``directory`` (normally ``data_dir / 'videos'``).

    ``list()`` includes invalid media with ``duration=None`` and ``error``.
    ``resolve(id)`` returns a confined file, not a promise of playability.
    ``items(ids)`` validates every selection and raises ValueError on failure.
    ``download(url, title)`` returns the initial job dict immediately;
    ``jobs()`` returns newest-first snapshots (at most 20). Progress is 0–100.
    Job statuses: queued, downloading, processing, completed, failed.
    """

    def __init__(self, directory: Path):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._cache: dict[str, tuple[tuple, float | None, str | None]] = {}
        self._thread: threading.Thread | None = None
        self._jobs: list[dict] = []
        self._jobs_path = self.directory / ".jobs.json"
        self._load_jobs()

    def _load_jobs(self):
        if not self._jobs_path.exists():
            return
        try:
            if self._jobs_path.is_symlink():
                raise ValueError("Job history must not be a symlink")
            data = json.loads(self._jobs_path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError("Invalid job history")
            for job in data[-_JOB_LIMIT:]:
                if (
                    not isinstance(job, dict)
                    or not isinstance(job.get("id"), str)
                    or not isinstance(job.get("title"), str)
                    or job.get("status") not in _ACTIVE | {"completed", "failed"}
                    or not isinstance(job.get("progress"), (float, int))
                    or not math.isfinite(job["progress"])
                    or not 0 <= job["progress"] <= 100
                    or not isinstance(job.get("error"), (str, type(None)))
                ):
                    raise ValueError("Invalid job history")
                self._jobs.append({key: job[key] for key in
                                   ("id", "title", "status", "progress", "error")})
            interrupted = False
            for job in self._jobs:
                if job["status"] in _ACTIVE:
                    job.update(status="failed", error="Download interrupted by application restart")
                    interrupted = True
            if interrupted:
                self._save_jobs()
        except (OSError, ValueError, TypeError, KeyError) as exc:
            _LOG.warning("Cannot restore video download history: %s", exc)
            self._jobs = [{
                "id": uuid.uuid4().hex, "title": "Download history", "status": "failed",
                "progress": 0, "error": f"Cannot restore download history: {exc}",
            }]

    def _save_jobs(self):
        temporary = self.directory / f".jobs-{uuid.uuid4().hex}.json"
        try:
            temporary.write_text(json.dumps(self._jobs), encoding="utf-8")
            os.replace(temporary, self._jobs_path)
        finally:
            temporary.unlink(missing_ok=True)

    def _files(self) -> dict[str, Path]:
        result = {}
        for path in self.directory.iterdir():
            if (
                path.suffix.lower() in _EXTENSIONS
                and not path.is_symlink()
                and path.is_file()
                and path.resolve().parent == self.directory
            ):
                result[hashlib.sha256(os.fsencode(path.name)).hexdigest()] = path
        return result

    @staticmethod
    def _probe(path: Path) -> float:
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-protocol_whitelist", "file,pipe", "-show_entries",
                 "format=duration:stream=codec_type,codec_name,duration",
                 "-of", "json", str(path)],
                capture_output=True, text=True, timeout=15, check=True,
            )
        except FileNotFoundError as exc:
            raise ValueError("ffprobe is missing; install FFmpeg and add it to PATH") from exc
        except subprocess.TimeoutExpired as exc:
            raise ValueError("ffprobe timed out while checking the video") from exc
        except (OSError, subprocess.CalledProcessError) as exc:
            raise ValueError("ffprobe could not read this video") from exc
        try:
            data = json.loads(result.stdout)
            streams = data["streams"]
            videos = [s for s in streams if s.get("codec_type") == "video"]
            audio = [s for s in streams if s.get("codec_type") == "audio"]
            if not videos:
                raise ValueError("Video has no video stream")
            if any(s.get("codec_name") not in _VIDEO_CODECS for s in videos):
                raise ValueError("Video codec is not browser compatible")
            if any(s.get("codec_name") not in _AUDIO_CODECS for s in audio):
                raise ValueError("Audio codec is not browser compatible")
            raw_duration = data.get("format", {}).get("duration")
            if raw_duration is None:
                raw_duration = videos[0].get("duration")
            duration = float(raw_duration)
            if not math.isfinite(duration) or duration <= 0:
                raise ValueError("Video duration must be finite and greater than zero")
            return duration
        except (KeyError, TypeError, AttributeError, json.JSONDecodeError) as exc:
            raise ValueError("ffprobe returned malformed video metadata or no duration") from exc
        except ValueError as exc:
            raise ValueError(f"Unplayable video: {exc}") from exc

    def _duration(self, path: Path) -> tuple[float | None, str | None]:
        try:
            stat = path.stat()
            signature = (stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns, stat.st_ino)
            cached = self._cache.get(path.name)
            if cached and cached[0] == signature:
                return cached[1], cached[2]
            try:
                duration, error = self._probe(path), None
            except ValueError as exc:
                duration, error = None, str(exc)
            self._cache[path.name] = (signature, duration, error)
            return duration, error
        except OSError as exc:
            return None, f"Cannot access video: {exc}"

    def _title(self, path: Path) -> str:
        metadata = path.with_suffix(".json")
        try:
            if metadata.is_symlink():
                return path.stem
            title = json.loads(metadata.read_text(encoding="utf-8"))["title"]
            return self._validate_title(title)
        except (OSError, ValueError, KeyError, TypeError):
            return path.stem

    def list(self) -> list[dict]:
        with self._lock:
            files = self._files()
            self._cache = {p.name: self._cache[p.name] for p in files.values()
                           if p.name in self._cache}
            items = []
            for identifier, path in files.items():
                duration, error = self._duration(path)
                item = {"id": identifier, "title": self._title(path), "duration": duration}
                if error:
                    item["error"] = error
                items.append(item)
            return sorted(items, key=lambda item: (item["title"].casefold(), item["id"]))

    def resolve(self, identifier: str) -> Path:
        with self._lock:
            if not isinstance(identifier, str) or not re.fullmatch(r"[0-9a-f]{64}", identifier):
                raise ValueError("Invalid video ID")
            path = self._files().get(identifier)
            if path is None:
                raise ValueError("Video not found")
            return path

    def items(self, identifiers) -> list[dict]:
        if not isinstance(identifiers, (list, tuple)):
            raise ValueError("Video IDs must be a list")
        with self._lock:
            selected = []
            for identifier in identifiers:
                path = self.resolve(identifier)
                duration, error = self._duration(path)
                if error or duration is None or duration <= 0:
                    raise ValueError(error or "Video has no valid duration")
                selected.append({"id": identifier, "title": self._title(path), "duration": duration})
            return selected

    def jobs(self) -> list[dict]:
        with self._lock:
            return [dict(job) for job in reversed(self._jobs)]

    @staticmethod
    def _validate_title(title: str) -> str:
        if not isinstance(title, str) or not title.strip() or len(title) > 120:
            raise ValueError("Title must contain 1–120 characters")
        if any(ord(char) < 32 or ord(char) == 127 for char in title):
            raise ValueError("Title must not contain control characters")
        return title.strip()

    @staticmethod
    def _validate_url(url: str) -> str:
        try:
            if not isinstance(url, str) or any(c.isspace() for c in url):
                raise ValueError("Invalid YouTube URL")
            parsed = urlsplit(url)
            if (
                parsed.scheme not in {"https", "http"}
                or parsed.netloc.lower() not in
                {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}
                or parsed.fragment
            ):
                raise ValueError("Use a single YouTube watch, shorts, or youtu.be URL")
            query = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True)
            if any(len(values) != 1 for values in query.values()):
                raise ValueError("Duplicate URL parameters are not allowed")
            if parsed.netloc.lower() == "youtu.be":
                identifier = parsed.path.removeprefix("/")
                allowed = {"t", "si"}
            elif parsed.path == "/watch":
                identifier = query.get("v", [""])[0]
                allowed = {"v", "t", "si"}
            elif parsed.path.startswith("/shorts/"):
                identifier = parsed.path[len("/shorts/"):]
                allowed = {"t", "si"}
            else:
                raise ValueError("Use a single YouTube video URL")
            if not set(query) <= allowed or not re.fullmatch(r"[A-Za-z0-9_-]{11}", identifier):
                raise ValueError("Invalid video ID or playlist URL")
            return f"https://www.youtube.com/watch?v={identifier}"
        except (TypeError, AttributeError) as exc:
            raise ValueError("Invalid YouTube URL") from exc

    def download(self, url: str, title: str) -> dict:
        url, title = self._validate_url(url), self._validate_title(title)
        with self._lock:
            if (any(job["status"] in _ACTIVE for job in self._jobs)
                    or (self._thread is not None and self._thread.is_alive())):
                raise ValueError("A video download is already active")
            job = {"id": uuid.uuid4().hex, "title": title, "status": "queued",
                   "progress": 0, "error": None}
            self._jobs = (self._jobs + [job])[-_JOB_LIMIT:]
            try:
                self._save_jobs()
                self._thread = threading.Thread(
                    target=self._worker, args=(job, url), daemon=True,
                    name=f"video-download-{job['id']}",
                )
                initial = dict(job)
                self._thread.start()
            except (OSError, RuntimeError) as exc:
                job.update(status="failed", error=f"Cannot start download: {exc}")
                raise ValueError(job["error"]) from exc
            return initial

    @staticmethod
    def _validate_download_info(info: dict, *, incomplete=False):
        if (not isinstance(info, dict) or info.get("_type") in {"playlist", "multi_video"}
                or "entries" in info):
            raise ValueError("Only a single video download is allowed")
        if info.get("is_live") or info.get("live_status") in {"is_live", "is_upcoming", "post_live"}:
            raise ValueError("Live, upcoming, or still-processing live videos cannot be downloaded")
        size = info.get("filesize") or info.get("filesize_approx") or 0
        if size > _MAX_DOWNLOAD_BYTES:
            raise ValueError("Video exceeds the 2 GiB download limit")

    def _check_space(self):
        if shutil.disk_usage(self.directory).free < _FREE_SPACE_RESERVE:
            raise ValueError("Insufficient free disk space; keep at least 256 MiB available")

    @classmethod
    def _match_filter(cls, info: dict, *, incomplete=False):
        try:
            cls._validate_download_info(info, incomplete=incomplete)
        except ValueError as exc:
            return str(exc)
        return None

    def _update(self, job: dict, **changes):
        with self._lock:
            if all(job.get(key) == value for key, value in changes.items()):
                return
            job.update(changes)
            self._save_jobs()

    def _worker(self, job: dict, url: str):
        staging = self.directory / ".downloads" / job["id"]
        published_metadata = None
        published = False
        staging_created = False
        try:
            import yt_dlp

            if staging.parent.is_symlink():
                raise ValueError("Download staging directory must not be a symlink")
            staging.parent.mkdir(exist_ok=True)
            if staging.parent.resolve().parent != self.directory:
                raise ValueError("Download staging directory escapes the video library")
            staging.mkdir()
            staging_created = True
            self._check_space()
            downloaded = {}
            stream_number = 0

            def progress(data):
                nonlocal stream_number
                self._check_space()
                key = data.get("filename") or str(stream_number)
                count = max(0, data.get("downloaded_bytes", 0))
                downloaded[key] = max(downloaded.get(key, 0), count)
                if sum(downloaded.values()) > _MAX_DOWNLOAD_BYTES:
                    raise ValueError("Download exceeds the cumulative 2 GiB limit")
                if data.get("status") == "finished":
                    self._update(job, status="processing", progress=100)
                    stream_number += 1
                elif data.get("status") == "downloading":
                    total = data.get("total_bytes") or data.get("total_bytes_estimate")
                    if total and total > _MAX_DOWNLOAD_BYTES:
                        raise ValueError("Video exceeds the 2 GiB download limit")
                    percent = min(99, max(0, int(100 * data.get("downloaded_bytes", 0) / total))) \
                        if total and total > 0 else 0
                    self._update(job, status="downloading", progress=percent)

            options = {
                "format": (
                    "bestvideo[ext=mp4][vcodec^=avc1][height<=1080]"
                    "+bestaudio[ext=m4a][acodec^=mp4a]/"
                    "best[ext=mp4][vcodec^=avc1][acodec^=mp4a][height<=1080]/"
                    "bestvideo[ext=webm][vcodec~='^(vp8|vp9|vp09|av01)'][height<=1080]"
                    "+bestaudio[ext=webm][acodec~='^(opus|vorbis)']/"
                    "best[ext=webm][vcodec~='^(vp8|vp9|vp09|av01)']"
                    "[acodec~='^(opus|vorbis)'][height<=1080]"
                ),
                "outtmpl": str(staging / "video.%(ext)s"),
                "merge_output_format": "mp4/webm",
                "noplaylist": True,
                "max_filesize": _MAX_DOWNLOAD_BYTES,
                "match_filter": self._match_filter,
                "break_on_reject": True,
                "ignoreerrors": False,
                "quiet": True,
                "no_warnings": True,
                "socket_timeout": 30,
                "retries": 2,
                "fragment_retries": 2,
                "concurrent_fragment_downloads": 1,
                "progress_hooks": [progress],
                "postprocessor_hooks": [
                    lambda _: self._update(job, status="processing", progress=100)
                ],
            }
            for name in ("deno", "deno.exe"):
                executable = Path(sys.executable).parent / name
                if executable.is_file():
                    options["js_runtimes"] = {"deno": {"path": str(executable)}}
                    break
            self._update(job, status="downloading")
            with yt_dlp.YoutubeDL(options) as downloader:
                info = downloader.extract_info(url, download=False)
                self._validate_download_info(info)
                downloader.extract_info(url, download=True)
            self._update(job, status="processing", progress=100)
            candidates = [p for p in staging.iterdir()
                          if p.suffix.lower() in _EXTENSIONS and p.is_file()
                          and not p.is_symlink() and p.resolve().parent == staging.resolve()]
            if len(candidates) != 1:
                raise ValueError("Download did not produce exactly one video")
            source = candidates[0]
            if source.stat().st_size > _MAX_DOWNLOAD_BYTES:
                raise ValueError("Completed video exceeds the 2 GiB download limit")
            self._check_space()
            self._probe(source)
            destination = self.directory / f"{job['id']}{source.suffix.lower()}"
            metadata = staging / "metadata.json"
            metadata.write_text(json.dumps({"title": job["title"]}), encoding="utf-8")
            published_metadata = destination.with_suffix(".json")
            os.replace(metadata, published_metadata)
            os.replace(source, destination)
            published = True
            self._update(job, status="completed", progress=100, error=None)
        except Exception as exc:
            # This is the thread boundary: third-party extractor/plugin failures
            # must become visible jobs, not uncaught exceptions in a daemon thread.
            _LOG.exception("Video download %s failed", job["id"])
            with self._lock:
                job.update(status="failed", error=f"{type(exc).__name__}: {exc}")
                try:
                    self._save_jobs()
                except OSError:
                    _LOG.exception("Cannot persist failed video download")
        finally:
            if not published and published_metadata is not None:
                try:
                    published_metadata.unlink(missing_ok=True)
                except OSError:
                    _LOG.exception("Cannot remove unpublished video metadata")
            # Never remove the shared staging root or follow a substituted symlink.
            if (staging_created and staging.exists() and not staging.is_symlink()
                    and not staging.parent.is_symlink()):
                try:
                    shutil.rmtree(staging)
                except OSError:
                    _LOG.exception("Cannot clean staging directory for %s", job["id"])
