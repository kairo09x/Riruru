from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls.types import MediaStream
import asyncio

# Note: Hum yahan 'ytdl' aur 'call_py' ko main.py se import karenge ya functions me pass karenge.
# Lekin sabse clean tarika hai ki hum main logic ko function me rakhein.

async def play_logic(client, message, ytdl, call_py):
    query = " ".join(message.command[1:])
    if not query:
        return await message.reply("Gane ka naam likho!")

    m = await message.reply("🔎 Searching...")
    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{query}", download=False))
        
        if not info or 'entries' not in info or not info['entries']:
            return await m.edit("❌ Song not found!")

        video = info['entries'][0]
        url = video['url']
        title = video['title']
        duration = video.get('duration_string', 'Unknown')
        thumbnail = video.get('thumbnail', 'https://telegra.ph/file/default.jpg')
        
        text = (
            f"★ **Sᴛᴀʀᴛᴇᴅ Sᴛʀᴇᴀᴍɪɴɢ Nᴏ** ★ ❞\n\n"
            f"★ **Tɪᴛʟᴇ** » {title[:40]}...\n"
            f"★ **Dᴜʀᴀᴛɪᴏɴ** » {duration} Mɪɴᴜᴛᴇs\n"
            f"★ **Bʏ** » {message.from_user.mention}\n\n"
            f"❖ **Mᴀᴅᴇ Bʏ** ➔ [TEAM PURVI BOTS](https://t.me/Team_Purvi_Bots) ❞"
        )
        
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Ⅱ", callback_data="pause"),
                InlineKeyboardButton("↻", callback_data="resume"),
                InlineKeyboardButton("‣I", callback_data="skip"),
                InlineKeyboardButton("▢", callback_data="stop")
            ]
        ])

        await call_py.play(message.chat.id, MediaStream(url))
        await m.delete()
        await message.reply_photo(photo=thumbnail, caption=text, reply_markup=buttons)

    except Exception as e:
        await m.edit(f"❌ Error: {str(e)[:100]}")

async def stop_logic(client, message, call_py):
    try:
        await call_py.leave_call(message.chat.id)
        await message.reply("⏹ Stopped.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
