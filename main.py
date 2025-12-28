import os
import asyncio
from dotenv import load_dotenv
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped
from yt_dlp import YoutubeDL

load_dotenv()

# Config
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
STRING_SESSION = os.getenv("STRING_SESSION")

# Clients
bot = Client("MusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
assistant = Client("Assistant", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
call_py = PyTgCalls(assistant)

ytdl_opts = {"format": "bestaudio/best", "quiet": True}
ytdl = YoutubeDL(ytdl_opts)

@bot.on_message(filters.command("play") & filters.group)
async def play_command(client, message):
    query = " ".join(message.command[1:])
    if not query:
        return await message.reply("Please provide a song name! Example: `/play Tum Hi Ho` ")

    m = await message.reply("🔎 Searching...")
    
    try:
        # Search and get stream link
        info = ytdl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
        url = info['url']
        title = info['title']
        
        await call_py.play(
            message.chat.id,
            AudioPiped(url)
        )
        await m.edit(f"🎶 **Playing:** {title}")
    except Exception as e:
        await m.edit(f"❌ Error: {e}")

@bot.on_message(filters.command("stop") & filters.group)
async def stop_command(client, message):
    try:
        await call_py.leave_call(message.chat.id)
        await message.reply("⏹ Stopped and Left VC.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

async def start_bot():
    await bot.start()
    await assistant.start()
    await call_py.start()
    print("Bot is Online!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(start_bot())
