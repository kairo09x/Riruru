from pyrogram.types import CallbackQuery
from pytgcalls.types import MediaStream
import asyncio
from commands import music_queues, play_next, send_now_playing, is_admin


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
    user_id = query.from_user.id

    if not await is_admin(client, chat_id, user_id):
        return await query.answer("🚫 Only admins can skip!", show_alert=True)

    queue = music_queues.get(chat_id)

    if not queue or len(queue) == 1:
        return await query.answer("No next song!", show_alert=True)

    await play_next(chat_id, call_py)
    await query.message.reply(
        f"⏭ **Sᴋɪᴘᴘᴇᴅ by [{query.from_user.first_name}](tg://user?id={user_id})**"
    )


async def stop_cb(client, query: CallbackQuery, call_py):
    chat_id = query.message.chat.id
    user_id = query.from_user.id

    if not await is_admin(client, chat_id, user_id):
        return await query.answer("🚫 Only admins can stop!", show_alert=True)

    music_queues.pop(chat_id, None)
    await call_py.leave_call(chat_id)

    await query.message.reply(
        f"⏹ **Sᴛᴏᴘᴘᴇᴅ by [{query.from_user.first_name}](tg://user?id={user_id})**"
    )

