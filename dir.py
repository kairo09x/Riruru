import shutil
from pathlib import Path


def ensure_dirs():
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg is not installed!")

    for folder in ("cache", "downloads"):
        Path(folder).mkdir(exist_ok=True)
