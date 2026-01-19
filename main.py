import os
import asyncio
from dotenv import load_dotenv
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from yt_dlp import YoutubeDL
from pytgcalls.types.stream import StreamEnded

# Command Imports
from commands import (
    play_logic, stop_logic, next_logic, play_next,
    songs_logic, pause_logic, resume_logic, playforce_logic,
    loop_logic, seek_logic
)

# Callback Imports
from callbacks import pause_cb, resume_cb, skip_cb, stop_cb

load_dotenv()

# --- Optimization: Increasing Workers ---
# 30k users ke liye workers 20+ rakhna zaruri hai
bot = Client(
    "MusicBot",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN"),
    workers=30 
)

assistant = Client(
    "Assistant",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    session_string=os.getenv("STRING_SESSION")
)

call_py = PyTgCalls(assistant)

# --- Optimized YTDL Instance ---
ytdl = YoutubeDL({
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "geo_bypass": True,
    "nocheckcertificate": True,
    "source_address": "0.0.0.0", # Faster connection
})

# --- Stream End Update ---
@call_py.on_update()
async def on_update_handler(client, update):
    if isinstance(update, StreamEnded):
        # asyncio.create_task use karein taaki update handler free rahe
        asyncio.create_task(play_next(update.chat_id, call_py, ytdl, bot))

# --- Callback Queries ---
@bot.on_callback_query(filters.regex("^(pause|resume|skip|stop)$"))
async def callbacks_handler(client, query):
    data = query.data
    if data == "pause":
        await pause_cb(client, query, call_py)
    elif data == "resume":
        await resume_cb(client, query, call_py)
    elif data == "skip":
        await skip_cb(client, query, call_py, ytdl)
    elif data == "stop":
        await stop_cb(client, query, call_py)

# --- Group Commands ---
@bot.on_message(filters.command(["play", "p"]) & filters.group)
async def play_cmd(client, message):
    await play_logic(client, assistant, message, ytdl, call_py)

@bot.on_message(filters.command("playforce") & filters.group)
async def playforce_cmd(client, message):
    await playforce_logic(client, assistant, message, ytdl, call_py)

@bot.on_message(filters.command(["stop", "end"]) & filters.group)
async def stop_cmd(client, message):
    await stop_logic(client, message, call_py)

@bot.on_message(filters.command(["skip", "next"]) & filters.group)
async def next_cmd(client, message):
    await next_logic(client, message, call_py, ytdl)

@bot.on_message(filters.command("pause") & filters.group)
async def pause_cmd(client, message):
    await pause_logic(client, message, call_py)

@bot.on_message(filters.command("resume") & filters.group)
async def resume_cmd(client, message):
    await resume_logic(client, message, call_py)

@bot.on_message(filters.command("loop") & filters.group)
async def loop_cmd(client, message):
    await loop_logic(client, message)

@bot.on_message(filters.command("seek") & filters.group)
async def seek_cmd(client, message):
    await seek_logic(client, message, call_py)

@bot.on_message(filters.command("songs") & filters.group)
async def songs_cmd(client, message):
    await songs_logic(client, message)

# --- Private Chat (Start) ---
@bot.on_message(filters.command("start") & filters.private)
async def start_private(client, message):
    user_name = message.from_user.first_name
    text = (
        f"★ **ʜᴇʟʟᴏ {user_name} !**\n\n"
        f"➤ **ɪ ᴀᴍ ᴀ ғᴀsᴛ ᴀɴᴅ ᴘᴏᴡᴇʀғᴜʟ ᴍᴜsɪᴄ ʙᴏᴛ.**\n"
        f"➤ **ᴜsᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ ᴇxᴘʟᴏʀᴇ ᴍᴏʀᴇ!**"
    )

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "➕ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ", 
                url=f"https://t.me/{bot.me.username}?startgroup=true"
            )
        ],
        [
            InlineKeyboardButton("📢 ᴜᴘᴅᴀᴛᴇs", url="https://t.me/ignovii"),
            InlineKeyboardButton("💗 ɴᴏʙɪᴛᴀ ᴋ", url="https://t.me/ig_novi")
        ]
    ])

    await message.reply_text(
        text=text,
        reply_markup=buttons,
        disable_web_page_preview=True
    )

# --- Bot Startup ---
async def start_bot():
    print("🚀 Starting Bot...")
    await bot.start()
    print("🤖 Starting Assistant...")
    await assistant.start()
    print("📞 Starting PyTgCalls...")
    await call_py.start()
    print("✅ Bot is online and optimized for 30k+ users!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(start_bot())
