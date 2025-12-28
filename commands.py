from pyrogram import filters
from bot import Bot
from calls import CallManager

player: CallManager = None


def setup(app: Bot, call_manager: CallManager):
    global player
    player = call_manager

    @app.on_message(filters.command("play") & filters.group)
    async def play(_, message):
        if len(message.command) < 2:
            return await message.reply("❌ Song name do")

        query = " ".join(message.command[1:])
        await player.play(message.chat.id, query)
        await message.reply(f"▶️ Playing: {query}")

    @app.on_message(filters.command("stop") & filters.group)
    async def stop(_, message):
        await player.stop(message.chat.id)
        await message.reply("⏹ Music stopped")
