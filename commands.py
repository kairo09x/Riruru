from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pytgcalls.types import MediaStream
import asyncio


# Note: Hum yahan 'ytdl' aur 'call_py' ko main.py se import karenge ya functions me pass karenge.
# Lekin sabse clean tarika hai ki hum main logic ko function me rakhein.

music_queues = {}

import logging
log = logging.getLogger(__name__)


from pyrogram.enums import ChatMemberStatus

async def is_admin(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        )
    except:
        return False
# from pytgcalls.types.stream import AudioPiped

async def play_next(chat_id, call_py):
    queue = music_queues.get(chat_id)
    log.info(f"📂 Queue before pop: {queue}")

    if not queue or len(queue) <= 1:
        music_queues.pop(chat_id, None)
        await call_py.leave_call(chat_id)
        log.info("🚪 Left call, queue empty")
        return

    # remove current song
    finished_song = queue.pop(0)
    next_song = queue[0]
    music_queues[chat_id] = queue  # update queue

    log.info(f"⏭️ Finished song: {finished_song['title']}")
    log.info(f"▶️ Next song: {next_song['title']} | Remaining queue: {len(queue)}")

    # 🔑 Use AudioPiped instead of MediaStream for pure audio
    # await call_py.change_stream(
    #     chat_id,
    #     AudioPiped(next_song["url"])
    # )
    await call_py.play(
        chat_id,
        MediaStream(next_song["url"])
    )


    log.info("✅ call_py.change_stream executed for next song")


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
    
    log.info(f"🎵 /play used in chat {chat_id} | query: {query}")

    if not query:
        log.warning("❌ Play command used without query")
        return await message.reply("❌ **Usage:** `/play song name`")

    m = await message.reply("🔎 **Searching...**")
    log.info("🔎 Searching started")

    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(
            None,
            lambda: ytdl.extract_info(
                f"ytsearch2:{query}",
                download=False
            )
        )
        log.info("🔍 Search completed")

        if not info or not info.get("entries"):
            log.warning("❌ Song not found")
            return await m.edit("❌ **Song not found!**")

        video = info["entries"][0]
        formats = video.get("formats", [])

        # ✅ 1. Try pure audio-only
        audio = next(
            (
                f for f in formats
                if f.get("acodec") != "none"
                and f.get("vcodec") == "none"
                and f.get("url")
            ),
            None
        )

        # ✅ 2. Fallback → any format with audio
        if not audio:
            audio = next(
                (
                    f for f in formats
                    if f.get("acodec") != "none"
                    and f.get("url")
                ),
                None
            )

        if not audio:
            log.error("❌ No playable audio stream found")
            return await m.edit("❌ **No playable audio stream found**")

        thumb = video.get("thumbnail") or \
            "https://telegra.ph/file/9c1b9b0c7f3c6c7a6c7d4.jpg"

        song = {
            "title": video.get("title", "Unknown"),
            "url": audio["url"],
            "duration": video.get("duration_string", "Unknown"),
            "thumbnail": thumb
        }

        queue = music_queues.get(chat_id, [])
        log.info(f"📂 Queue length before adding: {len(queue)}")

        # ➕ Queue logic
        if queue:
            if len(queue) >= 10:
                log.warning("🚫 Queue limit reached (10)")
                return await m.edit("🚫 **Queue limit reached (10)**")

            queue.append(song)
            music_queues[chat_id] = queue
            log.info(f"➕ Added to queue: {song['title']} | Position: {len(queue)}")
            return await m.edit(
                f"➕ **Added to queue**\n\n"
                f"🎵 {song['title'][:40]}...\n"
                f"📍 Position: {len(queue)}"
            )

        # ▶️ First song
        music_queues[chat_id] = [song]
        log.info(f"▶️ Playing first song: {song['title']}")

        await call_py.play(
            chat_id,
            MediaStream(song["url"])
        )
        log.info("✅ call_py.play executed")

        try:
            await m.delete()
        except:
            pass

        await send_now_playing(message, song)
        log.info("📢 Now playing message sent")

    except Exception as e:
        log.error(f"❌ Exception in play_logic: {e}")
        await m.edit(f"❌ **Error:** `{str(e)[:120]}`")




async def stop_logic(client, message, call_py):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if not await is_admin(client, chat_id, user_id):
        return await message.reply(
            "🚫 **Oɴʟʏ Aᴅᴍɪɴs Cᴀɴ Sᴛᴏᴘ Mᴜsɪᴄ!**"
        )

    try:
        music_queues.pop(chat_id, None)
        await call_py.leave_call(chat_id)

        await message.reply(
            f"⏹ **Sᴛᴏᴘᴘᴇᴅ by [{message.from_user.first_name}](tg://user?id={user_id})**",
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
    user_id = message.from_user.id

    if not await is_admin(client, chat_id, user_id):
        return await message.reply("🚫 **Oɴʟʏ Aᴅᴍɪɴs Cᴀɴ Sᴋɪᴘ Sᴏɴɢs!**")

    queue = music_queues.get(chat_id)

    if not queue or len(queue) == 1:
        return await message.reply("❌ **Nᴏ Nᴇxᴛ Sᴏɴɢ Iɴ Qᴜᴇᴜᴇ!**")

    await play_next(chat_id, call_py)
    await asyncio.sleep(1)

    song = music_queues[chat_id][0]
    await send_now_playing(message, song)


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
            None, lambda: ytdl.extract_info(f"ytsearch2:{query}", download=False)
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
        await call_py.play(
            chat_id,
            MediaStream(song["url"])
        )


        try:
            await message.delete()
            await m.delete()
        except:
            pass

        # 🎶 Same theme as /play
        await send_now_playing(message, song)

    except Exception as e:
        await message.reply(f"❌ **Eʀʀᴏʀ:** `{str(e)[:80]}`")

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
