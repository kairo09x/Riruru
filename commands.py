from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls.types import MediaStream
import asyncio
import logging

log = logging.getLogger(__name__)
music_queues = {}
loop_db = {} # Chat ID ke hisaab se True/False save karega

from pyrogram.enums import ChatMemberStatus

async def is_admin(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except:
        return False

async def loop_logic(client, message):
    chat_id = message.chat.id
    # if not await is_admin(client, chat_id, message.from_user.id):
    #     return await message.reply("🚫 **Only admins can use loop!**")

    if len(message.command) < 2:
        return await message.reply("❌ **Usage:** `/loop on` or `/loop off`")

    state = message.command[1].lower()
    if state == "on":
        loop_db[chat_id] = True
        await message.reply("🔄 **Loop Enabled!** Current song will play repeatedly.")
    elif state == "off":
        loop_db[chat_id] = False
        await message.reply("⏺ **Loop Disabled!** Playlist will continue normally.")
    else:
        await message.reply("❌ **Usage:** `/loop on` or `/loop off`")

# In imports ko upar add karein
from pyrogram.errors import WebpageMediaEmpty, MessageIdInvalid

async def send_now_playing(client, chat_id, song, requester_mention):
    text = (
        f"★ **Sᴛᴀʀᴛᴇᴅ Sᴛʀᴇᴀᴍɪɴɢ Nᴏᴡ** ★ ❞\n\n"
        f"★ **Tɪᴛʟᴇ** » {song['title'][:40]}...\n"
        f"★ **Dᴜʀᴀᴛɪᴏɴ** » {song['duration']} Mɪɴᴜᴛᴇs\n"
        f"★ **Bʏ** » {requester_mention}\n\n"
        f"❖ **Mᴀᴅᴇ Bʏ** ➔ [ᴺᵒ貴ᵗᵃ ᵏ](https://t.me/ig_novi) ❞"
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
        # Pehle photo bhejne ki koshish karein
        await client.send_photo(
            chat_id=chat_id,
            photo=song["thumbnail"],
            caption=text,
            reply_markup=buttons
        )
    except Exception as e:
        log.warning(f"Failed to send photo: {e}. Sending text instead.")
        # Agar photo fail ho jaye (WebpageMediaEmpty), toh bina thumbnail ke text bhej dein
        await client.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=buttons,
            disable_web_page_preview=True
        )




async def play_next(chat_id, call_py, ytdl, client):
    queue = music_queues.get(chat_id)
    is_loop = loop_db.get(chat_id, False) # Check karein loop on hai ya nahi

    if not queue:
        return

    if not is_loop:
        # Agar loop OFF hai, toh purana gaana hatao (Normal Behavior)
        queue.pop(0)
    else:
        # Agar loop ON hai, toh pop nahi karenge, wahi gaana index 0 par rahega
        log.info(f"🔄 Loop is ON for {chat_id}")

    if len(queue) == 0:
        music_queues.pop(chat_id, None)
        try: await call_py.leave_call(chat_id)
        except: pass
        return

    next_song = queue[0]
    
    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch1:{next_song['title']}", download=False))
        video = info["entries"][0]
        playable_url = next((f["url"] for f in video.get("formats", []) if f.get("acodec") != "none"), video["url"])

        await call_py.play(chat_id, MediaStream(playable_url))
        await send_now_playing(client, chat_id, next_song, next_song["requested_by"])
    except Exception as e:
        log.error(f"❌ Play Next Error: {e}")
        # Agar error aaye aur loop off ho tabhi pop karein warna infinite loop ho jayega
        if not is_loop: queue.pop(0)
        await play_next(chat_id, call_py, ytdl, client)

async def play_logic(client, assistant, message, ytdl, call_py):
    chat_id = message.chat.id
    query = " ".join(message.command[1:])
    
    try: await message.delete()
    except: pass

    if not query:
        return await client.send_message(chat_id, "❌ **Usage:** `/play song name`")

    m = await client.send_message(chat_id, "🔎 **Searching...**")
    
    try:
        # ... (Assistant join logic is same) ...
        try:
            await assistant.get_chat_member(chat_id, "me")
        except:
            try:
                chat = await client.get_chat(chat_id)
                link = chat.username if chat.username else await client.export_chat_invite_link(chat_id)
                await assistant.join_chat(link)
            except Exception as e:
                return await m.edit(f"❌ Assistant Error: {e}")

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
            "requested_by": message.from_user.mention 
        }

        queue = music_queues.get(chat_id, [])
        if queue:
            queue.append(song)
            await m.edit(f"➕ **Added to queue**\n\n🎵 {song['title'][:40]}...\n👤 By: {song['requested_by']}")
            await asyncio.sleep(5)
            try: await m.delete()
            except: pass
            return

        music_queues[chat_id] = [song]
        await call_py.play(chat_id, MediaStream(song["url"]))
        
        # Sukoon se delete karein
        try: await m.delete()
        except: pass

        await send_now_playing(client, chat_id, song, song["requested_by"])

    except Exception as e:
        log.error(f"❌ Play Logic Error: {e}")
        # FIXED: Check karein agar message exist karta hai tabhi edit karein
        try:
            await m.edit(f"❌ Error: {str(e)[:100]}")
        except MessageIdInvalid:
            # Agar message delete ho gaya hai, toh naya message bhej dein
            await client.send_message(chat_id, f"❌ Error: {str(e)[:100]}")



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

    # --- INSTANT DELETE COMMAND ---
    try:
        await message.delete()
    except Exception:
        pass # Permission nahi hai toh ignore karein

    if not query:
        return await client.send_message(
            chat_id, 
            "❌ **Uѕᴀɢᴇ:** `/playforce song name`"
        )

    # Search message ko 'm' variable mein save kiya
    m = await client.send_message(chat_id, "🔎 **Sᴇᴀʀᴄʜɪɴɢ...**")

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
            "requested_by": message.from_user.mention 
        }

        # --- QUEUE MANAGEMENT (Force Play Logic) ---
        if chat_id in music_queues:
            music_queues[chat_id].insert(0, song)
            if len(music_queues[chat_id]) > 1:
                music_queues[chat_id].pop(1) 
        else:
            music_queues[chat_id] = [song]

        # --- STREAMING ---
        try:
            await call_py.play(
                chat_id,
                MediaStream(song["url"])
            )
        except Exception as e:
            return await m.edit(f"❌ **Stream Error:** `{e}`")

        # Searching message delete karein
        try:
            await m.delete()
        except:
            pass

        # Notification notification bhejein
        await send_now_playing(client, chat_id, song, song["requested_by"])

    except Exception as e:
        log.error(f"❌ Force Play Error: {e}")
        await m.edit(f"❌ **Eʀʀᴏʀ:** `{str(e)[:100]}`")

async def seek_logic(client, message, call_py):
    chat_id = message.chat.id
    
    # # 1. Admin check
    # if not await is_admin(client, chat_id, message.from_user.id):
    #     return await message.reply("🚫 **Only admins can seek!**")

    # 2. Command format check
    if len(message.command) < 2:
        return await message.reply("❌ **Usage:** `/seek [seconds]`\nExample: `/seek 30` (to skip to 30th second)")

    query = message.command[1]
    if not query.isdigit():
        return await message.reply("❌ Please provide time in **seconds**.")

    seek_time = int(query)
    
    # 3. Check if song is playing
    queue = music_queues.get(chat_id)
    if not queue:
        return await message.reply("❌ Nothing is playing to seek.")

    current_song = queue[0]

    try:
        # PyTgCalls v3+ mein seek karne ka sahi tarika:
        # Hum wahi URL firse play karenge lekin 'ffmpeg_parameters' mein offset (ss) laga kar
        await call_py.play(
            chat_id,
            MediaStream(
                current_song["url"],
                ffmpeg_parameters=f"-ss {seek_time} -to {current_song.get('duration_seconds', 3600)}"
            )
        )
        await message.reply(f"⏩ **Seeked to {seek_time} seconds!**")
        
    except Exception as e:
        log.error(f"Seek Error: {e}")
        await message.reply(f"❌ **Error seeking:** `{str(e)[:50]}`")

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
    
    # Instant delete user command
    try: await message.delete()
    except: pass

    # # Admin check
    # if not await is_admin(client, chat_id, message.from_user.id):
    #     return await client.send_message(chat_id, "🚫 **Only admins can pause!**")

    # Check if anything is in queue
    if chat_id not in music_queues:
        return await client.send_message(chat_id, "❌ **Nothing is playing to pause.**")

    try:
        await call_py.pause(chat_id)
        await client.send_message(
            chat_id, 
            f"⏸ **Sᴛʀᴇᴀᴍ Pᴀᴜsᴇᴅ**\n└ By: {message.from_user.mention}"
        )
    except Exception as e:
        await client.send_message(chat_id, f"❌ **Error:** `{e}`")


async def resume_logic(client, message, call_py):
    chat_id = message.chat.id

    # Instant delete user command
    try: await message.delete()
    except: pass

    # # Admin check
    # if not await is_admin(client, chat_id, message.from_user.id):
    #     return await client.send_message(chat_id, "🚫 **Only admins can resume!**")

    # Check if anything is in queue
    if chat_id not in music_queues:
        return await client.send_message(chat_id, "❌ **Nothing is playing to resume.**")

    try:
        await call_py.resume(chat_id)
        await client.send_message(
            chat_id, 
            f"▶️ **Sᴛʀᴇᴀᴍ Rᴇsᴜᴍᴇᴅ**\n└ By: {message.from_user.mention}"
        )
    except Exception as e:
        await client.send_message(chat_id, f"❌ **Error:** `{e}`")
