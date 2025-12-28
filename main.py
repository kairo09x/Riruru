import os
import asyncio
from dotenv import load_dotenv
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from yt_dlp import YoutubeDL

# Commands import karein
from commands import play_logic, stop_logic

load_dotenv()

bot = Client("MusicBot", api_id=int(os.getenv("API_ID")), api_hash=os.getenv("API_HASH"), bot_token=os.getenv("BOT_TOKEN"))
assistant = Client("Assistant", api_id=int(os.getenv("API_ID")), api_hash=os.getenv("API_HASH"), session_string=os.getenv("STRING_SESSION"))
call_py = PyTgCalls(assistant)

ytdl = YoutubeDL({"format": "bestaudio/best", "quiet": True, "cookiefile": "cookies.txt"})

# --- Command Routing ---

@bot.on_message(filters.command("play") & filters.group)
async def play_cmd(client, message):
    await play_logic(client, message, ytdl, call_py)

@bot.on_message(filters.command("stop") & filters.group)
async def stop_cmd(client, message):
    await stop_logic(client, message, call_py)

# Yahan aap naye commands asani se add kar sakte hain:
# @bot.on_message(filters.command("help"))
# async def help_cmd(client, message):
#     await message.reply("Ye help menu hai...")

async def start_bot():
    await bot.start()
    await assistant.start()
    await call_py.start()
    print("✅ Bot is online with commands.py integrated!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(start_bot())
