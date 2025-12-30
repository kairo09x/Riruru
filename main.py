import os
import asyncio
from dotenv import load_dotenv
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from yt_dlp import YoutubeDL
from pytgcalls.types import Update
from pytgcalls.types.stream import StreamEnded


from commands import (
    play_logic, stop_logic, next_logic,
    songs_logic, pause_logic, resume_logic, playforce_logic
)

from callbacks import pause_cb, resume_cb, skip_cb, stop_cb
from player import play_next


load_dotenv()

bot = Client("MusicBot", api_id=int(os.getenv("API_ID")), api_hash=os.getenv("API_HASH"), bot_token=os.getenv("BOT_TOKEN"))
assistant = Client("Assistant", api_id=int(os.getenv("API_ID")), api_hash=os.getenv("API_HASH"), session_string=os.getenv("STRING_SESSION"))
call_py = PyTgCalls(assistant)


# @call_py.on_update()
# async def on_update_handler(client, update: Update):
#     if isinstance(update, StreamEnded):
#         await play_next(update.chat_id, call_py)


@call_py.on_update()
async def on_update_handler(client, update):
    if isinstance(update, StreamEnded):
        await play_next(update.chat_id, call_py)




# ytdl = YoutubeDL({"format": "bestaudio/best", "quiet": True, "cookiefile": "cookies.txt"})

ytdl = YoutubeDL({
    "format": "bestaudio/best",
    "quiet": True,
    "nocheckcertificate": True,
    "user_agent": "com.google.android.youtube/17.31.35",
    "extractor_args": {
        "youtube": {
            "player_client": ["android"]
        }
    }
})


# --- Command Routing ---


@bot.on_callback_query(filters.regex("^pause$"))
async def pause_btn(client, query):
    await pause_cb(client, query, call_py)

@bot.on_callback_query(filters.regex("^resume$"))
async def resume_btn(client, query):
    await resume_cb(client, query, call_py)

@bot.on_callback_query(filters.regex("^skip$"))
async def skip_btn(client, query):
    await skip_cb(client, query, call_py)

@bot.on_callback_query(filters.regex("^stop$"))
async def stop_btn(client, query):
    await stop_cb(client, query, call_py)


@bot.on_message(filters.command("play") & filters.group)
async def play_cmd(client, message):
    await play_logic(client, message, ytdl, call_py)

@bot.on_message(filters.command("playforce") & filters.group)
async def playforce_cmd(client, message):
    await playforce_logic(client, message, ytdl, call_py)

@bot.on_message(filters.command("pause") & filters.group)
async def pause_cmd(client, message):
    await pause_logic(client, message, call_py)

@bot.on_message(filters.command("resume") & filters.group)
async def resume_cmd(client, message):
    await resume_logic(client, message, call_py)

@bot.on_message(filters.command("stop") & filters.group)
async def stop_cmd(client, message):
    await stop_logic(client, message, call_py)

@bot.on_message(filters.command("next") & filters.group)
async def next_cmd(client, message):
    await next_logic(client, message, call_py)

@bot.on_message(filters.command("songs") & filters.group)
async def songs_cmd(client, message):
    await songs_logic(client, message)



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
