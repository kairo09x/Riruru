import yt_dlp
import os
import uuid


async def download_audio(query):
    file = f"downloads/{uuid.uuid4()}.mp3"

    ydl_opts = {
        "format": "bestaudio",
        "outtmpl": file,
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(query, download=True)

    return file
