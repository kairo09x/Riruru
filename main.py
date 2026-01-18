import os
import asyncio
from dotenv import load_dotenv
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from yt_dlp import YoutubeDL
from pytgcalls.types import Update
from pytgcalls.types.stream import StreamEnded


from commands import (
    play_logic, stop_logic, next_logic, play_next,
    songs_logic, pause_logic, resume_logic, playforce_logic
)

from callbacks import pause_cb, resume_cb, skip_cb, stop_cb
# from player import play_next


load_dotenv()

bot = Client("MusicBot", api_id=int(os.getenv("API_ID")), api_hash=os.getenv("API_HASH"), bot_token=os.getenv("BOT_TOKEN"))
assistant = Client("Assistant", api_id=int(os.getenv("API_ID")), api_hash=os.getenv("API_HASH"), session_string=os.getenv("STRING_SESSION"))
call_py = PyTgCalls(assistant)

@call_py.on_update()
async def on_update_handler(client, update):
    if isinstance(update, StreamEnded):
        # Yahan 'bot' pass karna zaruri hai taaki notification bhej sake
        # 'ytdl' ko bhi pass karein fresh link nikalne ke liye
        await play_next(update.chat_id, call_py, ytdl, bot)

ytdl = YoutubeDL({
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "geo_bypass": True,
    "nocheckcertificate": True,
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
    await skip_cb(client, query, call_py, ytdl)

@bot.on_callback_query(filters.regex("^stop$"))
async def stop_btn(client, query):
    await stop_cb(client, query, call_py)

@bot.on_message(filters.command("play") & filters.group)
async def play_cmd(client, message):
    # 'assistant' ko yahan pass karna zaruri hai
    await play_logic(client, assistant, message, ytdl, call_py)

@bot.on_message(filters.command("playforce") & filters.group)
async def playforce_cmd(client, message):
    # Assistant pass karna zaruri hai
    await playforce_logic(client, assistant, message, ytdl, call_py)

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
    # Yahan 'ytdl' pass karna zaruri hai kyunki next_logic ab ise mang raha hai
    await next_logic(client, message, call_py, ytdl)

@bot.on_message(filters.command("skip") & filters.group)
async def next_cmd(client, message):
    # Yahan 'ytdl' pass karna zaruri hai kyunki next_logic ab ise mang raha hai
    await next_logic(client, message, call_py, ytdl)

from commands import loop_logic, seek_logic, pause_logic, resume_logic

@bot.on_message(filters.command("loop") & filters.group)
async def loop_cmd(client, message):
    await loop_logic(client, message)

@bot.on_message(filters.command("seek") & filters.group)
async def seek_cmd(client, message):
    # 'call_py' pass karna zaroori hai seek karne ke liye
    await seek_logic(client, message, call_py)

@bot.on_message(filters.command(["pause", "resume"]) & filters.group)
async def pause_resume_cmds(client, message):
    if message.command[0].lower() == "pause":
        await pause_logic(client, message, call_py)
    else:
        await resume_logic(client, message, call_py)

@bot.on_message(filters.command("songs") & filters.group)
async def songs_cmd(client, message):
    await songs_logic(client, message)

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@bot.on_message(filters.command("start") & filters.private)
async def start_private(client, message):
    user_name = message.from_user.first_name # Ya mention use kar sakte hain
    
    # Simple stylish text bina photo ke
    text = (
        f"★ **ʜᴇʟʟᴏ {user_name} !**\n\n"
        f"➤ **ᴜsᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ ᴇxᴘʟᴏʀᴇ ᴍᴏʀᴇ!**"
    )

    # Buttons Layout: 1 upar, 2 niche
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

    try:
        # reply_photo ki jagah reply_text use kiya hai error se bachne ke liye
        await message.reply_text(
            text=text,
            reply_markup=buttons,
            disable_web_page_preview=True # Isse link ka bada preview nahi dikhega
        )
    except Exception as e:
        print(f"Error in start command: {e}")

async def start_bot():
    await bot.start()
    await assistant.start()
    await call_py.start()
    print("✅ Bot is online with commands.py integrated!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(start_bot())
