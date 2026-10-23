import json
from pathlib import Path
import shutil
import subprocess
import sys
import threading
from types import SimpleNamespace
import uuid

import pytest

from app.video_library import VideoLibrary


URL = "https://www.youtube.com/watch?v=abcdefghijk"


@pytest.fixture
def directory():
    # Keep all test artifacts inside the checkout rather than the OS temp folder.
    root = Path.cwd() / f".video-library-test-{uuid.uuid4().hex}"
    root.mkdir()
    yield root
    shutil.rmtree(root)


@pytest.fixture
def probe(monkeypatch):
    calls = []

    def run(arguments, **kwargs):
        calls.append((arguments, kwargs))
        return SimpleNamespace(stdout=json.dumps({
            "streams": [{"codec_type": "video", "codec_name": "h264"},
                        {"codec_type": "audio", "codec_name": "aac"}],
            "format": {"duration": "12.5"},
        }))

    monkeypatch.setattr("app.video_library.subprocess.run", run)
    return calls


def wait(library):
    library._thread.join(timeout=5)
    assert not library._thread.is_alive()
    return library.jobs()[0]


def fake_downloader(monkeypatch, action=None):
    captured = {}

    class Downloader:
        def __init__(self, options):
            captured.update(options)
            self.options = options

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def extract_info(self, url, download):
            assert url == URL
            if not download:
                return {"title": "Preflight metadata"}
            if action is not None:
                action(self.options)
            else:
                Path(self.options["outtmpl"].replace("%(ext)s", "mp4")).write_bytes(b"media")
            return {"title": "Untrusted extractor title"}

    monkeypatch.setitem(sys.modules, "yt_dlp", SimpleNamespace(YoutubeDL=Downloader))
    return captured


def test_index_ids_selection_and_probe_cache(directory, probe):
    library = VideoLibrary(directory)
    (directory / "z.MP4").write_bytes(b"a")
    (directory / "A.webm").write_bytes(b"b")
    (directory / "silent.m4v").write_bytes(b"c")
    (directory / "ignored.mkv").write_bytes(b"d")
    (directory / "nested").mkdir()
    (directory / "nested" / "hidden.mp4").write_bytes(b"e")
    items = library.list()
    assert [item["title"] for item in items] == ["A", "silent", "z"]
    assert all(len(item["id"]) == 64 and item["duration"] == 12.5 for item in items)
    assert library.resolve(items[0]["id"]) == directory / "A.webm"
    assert library.items([items[2]["id"], items[0]["id"]]) == [items[2], items[0]]
    library.list()
    assert len(probe) == 3
    (directory / "z.MP4").write_bytes(b"changed")
    library.list()
    assert len(probe) == 4
    assert probe[0][0][0] == "ffprobe"
    assert probe[0][1]["timeout"] == 15
    assert probe[0][1]["check"] is True
    (directory / "A.webm").unlink()
    with pytest.raises(ValueError, match="not found"):
        library.resolve(items[0]["id"])


@pytest.mark.parametrize("identifier", ["../secret.mp4", "C:\\secret.mp4", "", None, [], "a" * 64])
def test_resolve_rejects_external_and_unknown_ids(directory, identifier):
    with pytest.raises(ValueError):
        VideoLibrary(directory).resolve(identifier)


def test_symlinks_excluded_and_replacement_invalidates_id(directory, probe, monkeypatch):
    video = directory / "movie.mp4"
    video.write_bytes(b"media")
    library = VideoLibrary(directory)
    identifier = library.list()[0]["id"]
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda path: path == video or original(path))
    assert library.list() == []
    with pytest.raises(ValueError):
        library.resolve(identifier)


@pytest.mark.parametrize("payload, message", [
    ({"streams": [], "format": {"duration": "3"}}, "no video"),
    ({"streams": [{"codec_type": "video", "codec_name": "hevc"}],
      "format": {"duration": "3"}}, "Video codec"),
    ({"streams": [{"codec_type": "video", "codec_name": "h264"},
                 {"codec_type": "audio", "codec_name": "ac3"}],
      "format": {"duration": "3"}}, "Audio codec"),
    ({"streams": [{"codec_type": "video", "codec_name": "vp9"}],
      "format": {"duration": "NaN"}}, "duration"),
    ({"streams": [{"codec_type": "video", "codec_name": "vp9"}],
      "format": {"duration": "0"}}, "duration"),
    ({"streams": [{"codec_type": "video", "codec_name": "vp9"}]}, "duration"),
    ({"unexpected": True}, "malformed"),
])
def test_unplayable_media_is_visible_and_cannot_be_selected(directory, monkeypatch, payload, message):
    (directory / "broken.mp4").write_bytes(b"broken")
    monkeypatch.setattr("app.video_library.subprocess.run",
                        lambda *args, **kwargs: SimpleNamespace(stdout=json.dumps(payload)))
    library = VideoLibrary(directory)
    item = library.list()[0]
    assert item["duration"] is None
    assert message in item["error"]
    with pytest.raises(ValueError, match=message):
        library.items([item["id"]])


@pytest.mark.parametrize("failure, message", [
    (FileNotFoundError(), "ffprobe is missing"),
    (subprocess.TimeoutExpired("ffprobe", 15), "timed out"),
    (subprocess.CalledProcessError(1, "ffprobe"), "could not read"),
])
def test_probe_tool_errors_are_explicit(directory, monkeypatch, failure, message):
    (directory / "movie.mp4").write_bytes(b"media")

    def fail(*args, **kwargs):
        raise failure

    monkeypatch.setattr("app.video_library.subprocess.run", fail)
    assert message in VideoLibrary(directory).list()[0]["error"]


def test_malformed_probe_output_and_stream_duration(directory, monkeypatch):
    video = directory / "movie.webm"
    video.write_bytes(b"media")
    monkeypatch.setattr("app.video_library.subprocess.run",
                        lambda *a, **k: SimpleNamespace(stdout="not json"))
    assert "malformed" in VideoLibrary(directory).list()[0]["error"]
    monkeypatch.setattr("app.video_library.subprocess.run",
                        lambda *a, **k: SimpleNamespace(stdout=json.dumps({
                            "streams": [{"codec_type": "video", "codec_name": "av1",
                                         "duration": "2"}],
                        })))
    assert VideoLibrary(directory).list()[0]["duration"] == 2


@pytest.mark.parametrize("url", [
    URL, "http://youtube.com/watch?v=abcdefghijk",
    "https://youtu.be/abcdefghijk?si=share",
    "https://www.youtube.com/shorts/abcdefghijk",
    "https://m.youtube.com/watch?v=abcdefghijk&t=42",
])
def test_single_video_urls_are_canonicalized(url):
    assert VideoLibrary._validate_url(url) == URL


@pytest.mark.parametrize("url", [
    "https://evil.example/watch?v=abcdefghijk",
    "https://youtube.com.evil.example/watch?v=abcdefghijk",
    "https://user@youtube.com/watch?v=abcdefghijk",
    "https://youtube.com:443/watch?v=abcdefghijk",
    "https://youtube.com/playlist?list=abc",
    URL + "&list=abc", URL + "&v=abcdefghijk",
    URL + "#fragment", URL + "&bad", URL + "&list=",
    "https://youtu.be/abcdefghijk/extra", "file:///movie.mp4",
    "https://youtube.com/watch?v=short", "", None,
])
def test_invalid_urls_are_rejected_before_starting_worker(directory, url):
    library = VideoLibrary(directory)
    with pytest.raises(ValueError):
        library.download(url, "Title")
    assert library.jobs() == []


@pytest.mark.parametrize("title", ["", " ", "x" * 121, "Bad\nTitle", None])
def test_invalid_titles_are_rejected(directory, title):
    library = VideoLibrary(directory)
    with pytest.raises(ValueError):
        library.download(URL, title)
    assert library.jobs() == []


def test_success_atomic_publication_title_and_deno(directory, probe, monkeypatch):
    executable = directory / "python"
    executable.write_bytes(b"")
    (directory / "deno.exe").write_bytes(b"")
    monkeypatch.setattr(sys, "executable", str(executable))
    options = fake_downloader(monkeypatch)
    library = VideoLibrary(directory)
    initial = library.download(URL, "  Parent / chosen title  ")
    assert initial["status"] == "queued"
    job = wait(library)
    assert job["status"] == "completed"
    assert job["progress"] == 100 and job["error"] is None
    assert list((directory / ".downloads").iterdir()) == []
    item = library.list()[0]
    assert item["title"] == "Parent / chosen title"
    assert library.resolve(item["id"]).name == job["id"] + ".mp4"
    assert VideoLibrary(directory).list() == [item]
    assert VideoLibrary(directory).jobs() == [job]
    assert options["js_runtimes"] == {"deno": {"path": str(directory / "deno.exe")}}
    assert options["noplaylist"] is True
    assert options["merge_output_format"] == "mp4/webm"
    assert options["max_filesize"] == 2 * 1024**3
    assert "height<=1080" in options["format"]
    assert not {"cookies", "cookiefile", "remote_components"} & options.keys()


def test_progress_processing_and_single_active_worker(directory, probe, monkeypatch):
    downloading, proceed, processing, finish = (threading.Event() for _ in range(4))

    def action(options):
        options["progress_hooks"][0]({
            "status": "downloading", "downloaded_bytes": 25, "total_bytes": 100,
        })
        downloading.set()
        assert proceed.wait(5)
        options["progress_hooks"][0]({"status": "finished"})
        processing.set()
        assert finish.wait(5)
        Path(options["outtmpl"].replace("%(ext)s", "webm")).write_bytes(b"media")

    fake_downloader(monkeypatch, action)
    library = VideoLibrary(directory)
    library.download(URL, "A")
    try:
        assert downloading.wait(5)
        assert library.jobs()[0]["progress"] == 25
        assert library.jobs()[0]["status"] == "downloading"
        snapshot = library.jobs()
        snapshot[0]["status"] = "modified"
        with pytest.raises(ValueError, match="already active"):
            library.download(URL, "B")
        proceed.set()
        assert processing.wait(5)
        assert library.jobs()[0]["status"] == "processing"
        assert library.list() == []
    finally:
        proceed.set()
        finish.set()
        wait(library)
    assert library.jobs()[0]["status"] == "completed"


@pytest.mark.parametrize("failure", ["publication", "probe", "dependency", "extractor", "missing-output"])
def test_failed_download_is_explicit_and_never_published(directory, probe, monkeypatch, failure):
    fake_downloader(monkeypatch)
    if failure == "publication":
        import app.video_library as module
        replace = module.os.replace

        def fail_video(source, destination):
            if Path(destination).suffix == ".mp4":
                raise OSError("disk failure")
            replace(source, destination)

        monkeypatch.setattr(module.os, "replace", fail_video)
    elif failure == "probe":
        monkeypatch.setattr(VideoLibrary, "_probe",
                            staticmethod(lambda path: (_ for _ in ()).throw(ValueError("no duration"))))
    elif failure == "dependency":
        monkeypatch.setitem(sys.modules, "yt_dlp", None)
    elif failure == "extractor":
        def fail(options):
            raise RuntimeError("Extractor refused download")
        fake_downloader(monkeypatch, fail)
    else:
        fake_downloader(monkeypatch, lambda options: None)
    library = VideoLibrary(directory)
    library.download(URL, "A")
    job = wait(library)
    assert job["status"] == "failed" and job["error"]
    assert library.list() == []
    assert [path.name for path in directory.glob("*.json")] == [".jobs.json"]
    assert not (directory / ".downloads").exists() or not list((directory / ".downloads").iterdir())
    assert VideoLibrary(directory).jobs()[0]["status"] == "failed"


def test_restart_marks_interrupted_jobs_and_bounds_history(directory):
    history = [{"id": str(index), "title": str(index), "status": "completed",
                "progress": 100, "error": None} for index in range(25)]
    history[-1].update(status="downloading", progress=42)
    (directory / ".jobs.json").write_text(json.dumps(history), encoding="utf-8")
    library = VideoLibrary(directory)
    assert len(library.jobs()) == 20
    assert library.jobs()[0]["status"] == "failed"
    assert "interrupted" in library.jobs()[0]["error"]
    assert library.jobs()[0]["progress"] == 42
    assert VideoLibrary(directory).jobs() == library.jobs()


def test_invalid_history_does_not_break_startup(directory):
    (directory / ".jobs.json").write_text("broken", encoding="utf-8")
    library = VideoLibrary(directory)
    assert "history" in library.jobs()[0]["error"]


def test_invalid_metadata_falls_back_and_selection_shape(directory, probe):
    (directory / "movie.mp4").write_bytes(b"media")
    (directory / "movie.json").write_text('{"title": {"invalid": true}}', encoding="utf-8")
    library = VideoLibrary(directory)
    assert library.list()[0]["title"] == "movie"
    with pytest.raises(ValueError, match="list"):
        library.items("invalid")


@pytest.mark.parametrize("metadata", [
    {"_type": "playlist"}, {"entries": []}, {"is_live": True},
    {"live_status": "is_upcoming"}, {"live_status": "post_live"},
    {"filesize": 2 * 1024**3 + 1}, None,
])
def test_live_playlist_and_oversize_metadata_rejected(metadata):
    with pytest.raises(ValueError):
        VideoLibrary._validate_download_info(metadata)
    assert VideoLibrary._match_filter(metadata, incomplete=False)
    assert VideoLibrary._match_filter({"title": "ok"}, incomplete=True) is None


@pytest.mark.parametrize("reason", ["low-space", "cumulative", "estimated"])
def test_disk_limits_fail_explicitly_and_clean_staging(directory, probe, monkeypatch, reason):
    def action(options):
        hook = options["progress_hooks"][0]
        if reason == "cumulative":
            hook({"status": "downloading", "filename": "video",
                  "downloaded_bytes": 1024**3 + 1})
            hook({"status": "downloading", "filename": "audio",
                  "downloaded_bytes": 1024**3})
        else:
            hook({"status": "downloading", "downloaded_bytes": 0,
                  "total_bytes_estimate": 2 * 1024**3 + 1})

    fake_downloader(monkeypatch, action)
    if reason == "low-space":
        monkeypatch.setattr("app.video_library.shutil.disk_usage",
                            lambda _: SimpleNamespace(free=1))
    library = VideoLibrary(directory)
    library.download(URL, "A")
    job = wait(library)
    assert job["status"] == "failed"
    assert ("disk space" if reason == "low-space" else "2 GiB") in job["error"]
    assert library.list() == []
    assert list((directory / ".downloads").iterdir()) == []


def test_live_preflight_prevents_media_download(directory, monkeypatch):
    downloaded = []

    class LiveDownloader:
        def __init__(self, options):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def extract_info(self, url, download):
            if download:
                downloaded.append(url)
            return {"is_live": True}

    monkeypatch.setitem(sys.modules, "yt_dlp", SimpleNamespace(YoutubeDL=LiveDownloader))
    library = VideoLibrary(directory)
    library.download(URL, "Live")
    assert "Live" in wait(library)["error"]
    assert downloaded == []
