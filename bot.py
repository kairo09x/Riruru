from pyrogram import Client, enums
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_ID, LOGGER_ID
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class Bot(Client):
    def __init__(self):
        super().__init__(
            name="MyMusicBot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            parse_mode=enums.ParseMode.HTML,
        )

        self.owner_id = OWNER_ID
        self.logger_id = LOGGER_ID

    async def start(self):
        await super().start()
        me = await self.get_me()
        log.info(f"Started as @{me.username}")

        if self.logger_id:
            try:
                await self.send_message(self.logger_id, "🎵 Music Bot Started")
            except Exception as e:
                log.warning(f"Logger group error: {e}")

    async def stop(self):
        await super().stop()
        log.info("Bot stopped")
