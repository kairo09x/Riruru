LANG = {
    "play": "▶️ Playing: {title}",
    "skip": "⏭ Skipped",
    "stop": "⏹ Stopped",
    "no_song": "❌ No song in queue",
}


def get(key, **kwargs):
    return LANG[key].format(**kwargs)
