from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN


class Bot(Client):
    def __init__(self):
        super().__init__(
            "AudioMusicBot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
        )
