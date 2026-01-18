from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls.types import MediaStream
import asyncio
import logging

log = logging.getLogger(__name__)
music_queues = {}

from pyrogram.enums import ChatMemberStatus

async def is_admin(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except:
        return False

# --- FIXED: 4 arguments support karne ke liye update kiya ---
async def send_now_playing(client, chat_id, song, requester_mention):
    text = (
        f"★ **Sᴛᴀʀᴛᴇᴅ Sᴛʀᴇᴀᴍɪɴɢ Nᴏᴡ** ★ ❞\n\n"
        f"★ **Tɪᴛʟᴇ** » {song['title'][:40]}...\n"
        f"★ **Dᴜʀᴀᴛɪᴏɴ** » {song['duration']} Mɪɴᴜᴛᴇs\n"
        f"★ **Bʏ** » {requester_mention}\n\n"
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

    await client.send_photo(
        chat_id=chat_id,
        photo=song["thumbnail"],
        caption=text,
        reply_markup=buttons
    )

async def play_next(chat_id, call_py, ytdl, client):
    queue = music_queues.get(chat_id)
    
    if not queue or len(queue) <= 1:
        music_queues.pop(chat_id, None)
        try:
            await call_py.leave_call(chat_id)
        except:
            pass
        return

    queue.pop(0)
    next_song = queue[0]
    
    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(
            None, 
            lambda: ytdl.extract_info(f"ytsearch1:{next_song['title']}", download=False)
        )
        video = info["entries"][0]
        formats = video.get("formats", [])
        playable_url = next((f["url"] for f in formats if f.get("acodec") != "none"), video["url"])

        await call_py.play(chat_id, MediaStream(playable_url))
        
        # Requester mention ko queue se nikal kar notify kiya
        await send_now_playing(client, chat_id, next_song, next_song["requested_by"])
        log.info(f"✅ Auto-playing next: {next_song['title']}")

    except Exception as e:
        log.error(f"❌ Auto-play error: {e}")
        await play_next(chat_id, call_py, ytdl, client)

async def play_logic(client, assistant, message, ytdl, call_py):
    chat_id = message.chat.id
    query = " ".join(message.command[1:])
    
    if not query:
        return await message.reply("❌ **Usage:** `/play song name`")

    m = await message.reply("🔎 **Searching...**")
    
    # Assistant join logic (shortened for clarity)
    try:
        await assistant.get_chat_member(chat_id, "me")
    except:
        try:
            chat = await client.get_chat(chat_id)
            link = chat.username if chat.username else await client.export_chat_invite_link(chat_id)
            await assistant.join_chat(link)
        except Exception as e:
            return await m.edit(f"❌ Assistant Error: {e}")

    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch2:{query}", download=False))

        if not info or not info.get("entries"):
            return await m.edit("❌ **Song not found!**")

        video = info["entries"][0]
        formats = video.get("formats", [])
        audio_url = next((f["url"] for f in formats if f.get("acodec") != "none"), video["url"])

        song = {
            "title": video.get("title", "Unknown"),
            "url": audio_url,
            "duration": video.get("duration_string", "Unknown"),
            "thumbnail": video.get("thumbnail") or "https://telegra.ph/file/9c1b9b0c7f3c6c7a6c7d4.jpg",
            "requested_by": message.from_user.mention # <--- Save mention here
        }

        queue = music_queues.get(chat_id, [])
        if queue:
            queue.append(song)
            return await m.edit(f"➕ **Added to queue**\n\n🎵 {song['title'][:40]}...\n👤 By: {song['requested_by']}")

        music_queues[chat_id] = [song]
        await call_py.play(chat_id, MediaStream(song["url"]))
        await m.delete()

        await send_now_playing(client, chat_id, song, song["requested_by"])

    except Exception as e:
        await m.edit(f"❌ Error: {e}")

async def next_logic(client, message, call_py, ytdl):
    chat_id = message.chat.id
    if not await is_admin(client, chat_id, message.from_user.id):
        return await message.reply("🚫 Admin only!")

    queue = music_queues.get(chat_id)
    if not queue or len(queue) <= 1:
        return await message.reply("❌ No next song!")

    # FIXED: play_next ko client pass kiya taaki ye bhi notification bhej sake
    await play_next(chat_id, call_py, ytdl, client)


async def playforce_logic(client, assistant, message, ytdl, call_py):
    chat_id = message.chat.id
    query = " ".join(message.command[1:])

    if not query:
        return await message.reply("❌ **Uѕᴀɢᴇ:** `/playforce song name`")

    m = await message.reply("🔎 **Sᴇᴀʀᴄʜɪɴɢ...**")

    # --- ASSISTANT AUTO-JOIN ---
    try:
        await assistant.get_chat_member(chat_id, "me")
    except Exception:
        try:
            chat = await client.get_chat(chat_id)
            link = chat.username if chat.username else await client.export_chat_invite_link(chat_id)
            await assistant.join_chat(link)
        except Exception as e:
            return await m.edit(f"❌ **Assistant join nahi kar paya:** `{e}`")

    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(f"ytsearch2:{query}", download=False)
        )

        if not info or not info.get("entries"):
            return await m.edit("**Sᴏɴɢ ɴᴏᴛ ғᴏᴜɴᴅ!**")

        video = info["entries"][0]
        formats = video.get("formats", [])
        audio_url = next((f["url"] for f in formats if f.get("acodec") != "none"), video["url"])
        thumb = video.get("thumbnail") or "https://telegra.ph/file/9c1b9b0c7f3c6c7a6c7d4.jpg"

        song = {
            "title": video["title"],
            "url": audio_url,
            "duration": video.get("duration_string", "Unknown"),
            "thumbnail": thumb,
            "requested_by": message.from_user.mention # Requester mention add kiya
        }

        # --- QUEUE MANAGEMENT (Force Play Logic) ---
        if chat_id in music_queues:
            # Sirf current song (index 0) ko hatao aur naya gana index 0 par dalo
            # Taki baki bache hue gane line mein hi rahein
            music_queues[chat_id].insert(0, song)
            if len(music_queues[chat_id]) > 1:
                music_queues[chat_id].pop(1) # Purana playing song hat gaya
        else:
            music_queues[chat_id] = [song]

        # --- STREAMING ---
        try:
            # Purana stream reset karne ke liye change_stream ya leave use karein
            await call_py.play(
                chat_id,
                MediaStream(song["url"])
            )
        except Exception as e:
            return await m.edit(f"❌ **Stream Error:** `{e}`")

        try:
            await m.delete()
        except:
            pass

        # --- FIXED: Sahi arguments pass kiye notification ke liye ---
        await send_now_playing(client, chat_id, song, song["requested_by"])

    except Exception as e:
        log.error(f"❌ Force Play Error: {e}")
        await m.edit(f"❌ **Eʀʀᴏʀ:** `{str(e)[:100]}`")


async def songs_logic(client, message):
    chat_id = message.chat.id
    queue = music_queues.get(chat_id)

    if not queue:
        return await message.reply("📭 **Qᴜᴇᴜᴇ Iᴛ Eᴍᴘᴛʏ!**")

    text = "🎶 **Qᴜᴇᴜᴇᴅ Sᴏɴɢs** ❞\n\n"

    for i, song in enumerate(queue, start=1):
        text += f"★ {i}. {song['title'][:45]}...\n"

    await message.reply(text)


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
