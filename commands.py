from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pytgcalls.types import MediaStream
import asyncio
from main import call_py


# Note: Hum yahan 'ytdl' aur 'call_py' ko main.py se import karenge ya functions me pass karenge.
# Lekin sabse clean tarika hai ki hum main logic ko function me rakhein.

music_queues = {}

async def is_admin(client, chat_id, user_id):
    member = await client.get_chat_member(chat_id, user_id)
    return member.status in ("administrator", "creator")


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

async def send_now_playing(message, song):
    text = (
        f"★ **Sᴛᴀʀᴛᴇᴅ Sᴛʀᴇᴀᴍɪɴɢ Nᴏ** ★ ❞\n\n"
        f"★ **Tɪᴛʟᴇ** » {song['title'][:40]}...\n"
        f"★ **Dᴜʀᴀᴛɪᴏɴ** » {song['duration']} Mɪɴᴜᴛᴇs\n"
        f"★ **Bʏ** » {message.from_user.mention}\n\n"
        f"❖ **Mᴀᴅᴇ Bʏ** ➔ [ᴺᵒᵇⁱᵗᵃ ᵏ](https://t.me/ig_novi) ❞"
    )

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Ⅱ", callback_data="pause"),
            InlineKeyboardButton("↻", callback_data="resume"),
            InlineKeyboardButton("‣I", callback_data="skip"),
            InlineKeyboardButton("▢", callback_data="stop")
        ]
    ])

    await message.reply_photo(
        photo=song["thumbnail"],
        caption=text,
        reply_markup=buttons
    )


async def play_logic(client, message, ytdl, call_py):
    chat_id = message.chat.id
    query = " ".join(message.command[1:])

    if not query:
        return await message.reply(
            "❌ **Uѕᴀɢᴇ:** `/play song name`",
            disable_web_page_preview=True
        )

    m = await message.reply("🔎 **Sᴇᴀʀᴄʜɪɴɢ...**")

    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(f"ytsearch:{query}", download=False)
        )

        if not info or not info.get("entries"):
            return await m.edit("❌ **Sᴏɴɢ ɴᴏᴛ ғᴏᴜɴᴅ!**")

        video = info["entries"][0]

        thumb = video.get("thumbnail")
        if not thumb or not thumb.startswith("http"):
            thumb = "https://telegra.ph/file/9c1b9b0c7f3c6c7a6c7d4.jpg"

        song = {
            "title": video["title"],
            "url": video["url"],
            "duration": video.get("duration_string", "Unknown"),
            "thumbnail": thumb
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
            f"❖ **Mᴀᴅᴇ Bʏ** ➔ [ᴺᵒᵇⁱᵗᵃ ᵏ](https://t.me/ig_novi) ❞"
        )

        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Ⅱ", callback_data="pause"),
                InlineKeyboardButton("↻", callback_data="resume"),
                InlineKeyboardButton("‣I", callback_data="skip"),
                InlineKeyboardButton("▢", callback_data="stop")
            ]
        ])


        try:
            await m.delete()
        except:
            pass
        await send_now_playing(message, song)


    except Exception as e:
        await message.reply(f"❌ **Eʀʀᴏʀ:** `{str(e)[:80]}`")


async def stop_logic(client, message, call_py):
    chat_id = message.chat.id
    try:
        music_queues.pop(chat_id, None)
        await call_py.leave_call(chat_id)
        await message.reply(
            f"⏹ **Sᴛᴏᴘᴘᴇᴅ by [{message.from_user.first_name}](tg://user?id={message.from_user.id})**",
            disable_web_page_preview=True
        )
    except Exception as e:
        await message.reply(f"❌ **Eʀʀᴏʀ:** `{e}`")




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
    await asyncio.sleep(1)

    song = music_queues[chat_id][0]
    await send_now_playing(message, song)

async def pause_logic(client, message, call_py):
    chat_id = message.chat.id
    try:
        await call_py.pause_stream(chat_id)
        await message.reply(
            f"⏸ **Pᴀᴜsᴇᴅ by [{message.from_user.first_name}](tg://user?id={message.from_user.id})**"
        )
    except Exception:
        await message.reply("❌ **Nᴏᴛʜɪɴɢ ᴛᴏ Pᴀᴜsᴇ!**")

async def resume_logic(client, message, call_py):
    chat_id = message.chat.id
    try:
        await call_py.resume_stream(chat_id)
        await message.reply(
            f"▶️ **Rᴇsᴜᴍᴇᴅ by [{message.from_user.first_name}](tg://user?id={message.from_user.id})**"
        )
    except Exception:
        await message.reply("❌ **Nᴏᴛʜɪɴɢ ᴛᴏ Rᴇsᴜᴍᴇ!**")

async def playforce_logic(client, message, ytdl, call_py):
    chat_id = message.chat.id
    query = " ".join(message.command[1:])

    if not query:
        return await message.reply(
            "❌ **Uѕᴀɢᴇ:** `/playforce song name`",
            disable_web_page_preview=True
        )

    m = await message.reply("🔎 **Sᴇᴀʀᴄʜɪɴɢ...**")

    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(f"ytsearch:{query}", download=False)
        )

        if not info or not info.get("entries"):
            return await m.edit("❌ **Sᴏɴɢ ɴᴏᴛ ғᴏᴜɴᴅ!**")

        video = info["entries"][0]

        thumb = video.get("thumbnail")
        if not thumb or not thumb.startswith("http"):
            thumb = "https://telegra.ph/file/9c1b9b0c7f3c6c7a6c7d4.jpg"

        song = {
            "title": video["title"],
            "url": video["url"],
            "duration": video.get("duration_string", "Unknown"),
            "thumbnail": thumb
        }

        # 🔴 Force stop current stream
        await call_py.leave_call(chat_id)
        await asyncio.sleep(1)

        # ▶️ Play forced song
        await call_py.play(chat_id, MediaStream(song["url"]))

        # 🔁 Replace only current song, keep queue untouched
        if chat_id in music_queues and music_queues[chat_id]:
            music_queues[chat_id][0] = song
        else:
            music_queues[chat_id] = [song]

        try:
            await m.delete()
        except:
            pass

        # 🎶 Same theme as /play
        await send_now_playing(message, song)

    except Exception as e:
        await message.reply(f"❌ **Eʀʀᴏʀ:** `{str(e)[:80]}`")
