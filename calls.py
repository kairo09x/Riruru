from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, AudioQuality
from utils import download_audio
from queue import clear


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

    async def stop(self, chat_id):
        clear(chat_id)
        await self.call.leave_call(chat_id)
)
