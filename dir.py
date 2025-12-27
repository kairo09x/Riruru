import shutil
from pathlib import Path


def ensure_dirs():
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg not installed!")

    Path("downloads").mkdir(exist_ok=True)
