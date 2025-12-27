import os

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID = int(os.getenv("OWNER_ID", 0))
LOGGER_ID = int(os.getenv("LOGGER_ID", 0))

DEFAULT_THUMB = os.getenv(
    "DEFAULT_THUMB",
    "https://telegra.ph/file/8b3f6c7e6a9a6b0b5c.jpg"
)

SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "https://t.me/")
