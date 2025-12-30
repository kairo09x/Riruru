from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls.types import MediaStream
import asyncio


# Note: Hum yahan 'ytdl' aur 'call_py' ko main.py se import karenge ya functions me pass karenge.
# Lekin sabse clean tarika hai ki hum main logic ko function me rakhein.

music_queues = {}

async def play_next(chat_id, call_py):
    queue = music_queues.get(chat_id)

    if not queue or len(queue) == 1:
        music_queues.pop(chat_id, None)
        await call_py.leave_call(chat_id)
        return

    # remove current song
    queue.pop(0)
    next_song = queue[0]

    # restart stream with next song
    await call_py.leave_call(chat_id)
    await asyncio.sleep(1)
    await call_py.play(chat_id, MediaStream(next_song["url"]))


async def play_logic(client, message, ytdl, call_py):
    chat_id = message.chat.id
    query = " ".join(message.command[1:])
    if not query:
        return await message.reply("❌ **Gᴀɴᴇ ᴋᴀ ɴᴀᴀᴍ ʟɪᴋʜᴏ!**")

    m = await message.reply("🔎 **Sᴇᴀʀᴄʜɪɴɢ...**")

    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(f"ytsearch:{query}", download=False)
        )

        if not info or not info.get("entries"):
            return await m.edit("❌ **Sᴏɴɢ ɴᴏᴛ ғᴏᴜɴᴅ!**")

        video = info["entries"][0]

        song = {
            "title": video["title"],
            "url": video["url"],
            "duration": video.get("duration_string", "Unknown"),
            "thumbnail": video.get("thumbnail", "https://telegra.ph/file/default.jpg")
        }

        queue = music_queues.get(chat_id, [])

        # ➕ Add to queue if already playing
        if queue:
            if len(queue) >= 10:
                return await m.edit("🚫 **Qᴜᴇᴜᴇ Lɪᴍɪᴛ Rᴇᴀᴄʜᴇᴅ (10)**")

            queue.append(song)
            music_queues[chat_id] = queue

            return await m.edit(
                f"➕ **Aᴅᴅᴇᴅ Tᴏ Qᴜᴇᴜᴇ** ❞\n\n"
                f"★ **Tɪᴛʟᴇ** » {song['title'][:40]}...\n"
                f"★ **Pᴏsɪᴛɪᴏɴ** » {len(queue)}"
            )

        # ▶️ First song
        music_queues[chat_id] = [song]
        await call_py.play(chat_id, MediaStream(song["url"]))

        text = (
            f"★ **Sᴛᴀʀᴛᴇᴅ Sᴛʀᴇᴀᴍɪɴɢ Nᴏ** ★ ❞\n\n"
            f"★ **Tɪᴛʟᴇ** » {song['title'][:40]}...\n"
            f"★ **Dᴜʀᴀᴛɪᴏɴ** » {song['duration']} Mɪɴᴜᴛᴇs\n"
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

        await m.delete()
        await message.reply_photo(
            photo=song["thumbnail"],
            caption=text,
            reply_markup=buttons
        )

    except Exception as e:
        await m.edit(f"❌ **Eʀʀᴏʀ:** `{str(e)[:80]}`")


async def stop_logic(client, message, call_py):
    try:
        await call_py.leave_call(message.chat.id)
        await message.reply("⏹ Stopped.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


async def songs_logic(client, message):
    chat_id = message.chat.id
    queue = music_queues.get(chat_id)

    if not queue:
        return await message.reply("📭 **Qᴜᴇᴜᴇ Iᴛ Eᴍᴘᴛʏ!**")

    text = "🎶 **Qᴜᴇᴜᴇᴅ Sᴏɴɢs** ❞\n\n"

    for i, song in enumerate(queue, start=1):
        text += f"★ {i}. {song['title'][:45]}...\n"

    await message.reply(text)


async def next_logic(client, message, call_py):
    chat_id = message.chat.id
    queue = music_queues.get(chat_id)

    if not queue or len(queue) == 1:
        return await message.reply("❌ **Nᴏ Nᴇxᴛ Sᴏɴɢ Iɴ Qᴜᴇᴜᴇ!**")

    await play_next(chat_id, call_py)
    await message.reply(
        f"⏭ **Nᴏᴡ Pʟᴀʏɪɴɢ** ❞\n\n"
        f"★ **Tɪᴛʟᴇ** » {music_queues[chat_id][0]['title'][:40]}..."
    )


