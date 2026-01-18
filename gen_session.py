from pyrogram import Client

api_id = YOUR_API_ID
api_hash = "YOUR_API_HASH"

with Client("gen", api_id=api_id, api_hash=api_hash) as app:
    print(app.export_session_string())
