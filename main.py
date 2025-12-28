from bot import Bot
from calls import CallManager
from dir import ensure_dirs
import commands

app = Bot()
player = CallManager(app)

ensure_dirs()
commands.setup(app, player)

app.run()
