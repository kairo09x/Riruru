# player.py
import asyncio
from pytgcalls.types import MediaStream

music_queues = {}

async def play_next(chat_id, call_py):
    queue = music_queues.get(chat_id)

    if not queue or len(queue) == 1:
        music_queues.pop(chat_id, None)
        await call_py.leave_call(chat_id)
        return

    queue.pop(0)
    next_song = queue[0]

    await call_py.leave_call(chat_id)
    await asyncio.sleep(1)
    await call_py.play(chat_id, MediaStream(next_song["url"]))
