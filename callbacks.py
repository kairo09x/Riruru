from pyrogram.types import CallbackQuery
from pytgcalls.types import MediaStream
import asyncio
from commands import music_queues, play_next, send_now_playing


async def pause_cb(client, query: CallbackQuery, call_py):
    chat_id = query.message.chat.id
    await call_py.pause_stream(chat_id)
    await query.message.reply(
        f"⏸ **Pᴀᴜsᴇᴅ by {query.from_user.mention}**"
    )
    await query.answer()


async def resume_cb(client, query: CallbackQuery, call_py):
    chat_id = query.message.chat.id
    await call_py.resume_stream(chat_id)
    await query.message.reply(
        f"▶️ **Rᴇsᴜᴍᴇᴅ by {query.from_user.mention}**"
    )
    await query.answer()


async def skip_cb(client, query: CallbackQuery, call_py):
    chat_id = query.message.chat.id

    member = await client.get_chat_member(chat_id, query.from_user.id)
    if member.status not in ("administrator", "creator"):
        return await query.answer("❌ Admin only", show_alert=True)

    await play_next(chat_id, call_py)
    song = music_queues[chat_id][0]
    await send_now_playing(query.message, song)
    await query.answer("⏭ Skipped")


async def stop_cb(client, query: CallbackQuery, call_py):
    chat_id = query.message.chat.id

    member = await client.get_chat_member(chat_id, query.from_user.id)
    if member.status not in ("administrator", "creator"):
        return await query.answer("❌ Admin only", show_alert=True)

    music_queues.pop(chat_id, None)
    await call_py.leave_call(chat_id)

    await query.message.reply(
        f"⏹ **Sᴛᴏᴘᴘᴇᴅ by {query.from_user.mention}**"
    )
    await query.answer()
