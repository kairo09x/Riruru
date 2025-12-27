from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, AudioQuality
from queue import get_next, clear
from utils import download_audio


class CallManager:
    def __init__(self, app):
        self.call = PyTgCalls(app)

    async def start(self):
        await self.call.start()

    async def play(self, chat_id, query):
        file = await download_audio(query)
        stream = MediaStream(
            media_path=file,
            audio_parameters=AudioQuality.HIGH,
        )
        await self.call.play(chat_id, stream)

    async def skip(self, chat_id):
        next_track = get_next(chat_id)
        if not next_track:
            await self.call.leave_call(chat_id)
            return False
        await self.play(chat_id, next_track)
        return True

    async def stop(self, chat_id):
        clear(chat_id)
        await self.call.leave_call(chat_id)
