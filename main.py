from bot import Bot
from calls import CallManager
from dir import ensure_dirs
import commands

app = Bot()
player = CallManager(app)

ensure_dirs()


async def start_all():
    await app.start()
    await player.start()
    await idle()


if __name__ == "__main__":
    app.run()
