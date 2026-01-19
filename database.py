import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Memory Cache: { chat_id: {user_id1, user_id2} }
auth_cache = {}

def load_auth_users():
    """Bot start hote hi database se data load karega"""
    response = supabase.table("auth_users").select("chat_id, user_id").execute()
    for row in response.data:
        cid = row["chat_id"]
        uid = row["user_id"]
        if cid not in auth_cache:
            auth_cache[cid] = set()
        auth_cache[cid].add(uid)

def add_auth_user(chat_id, user_id):
    supabase.table("auth_users").insert({"chat_id": chat_id, "user_id": user_id}).execute()
    if chat_id not in auth_cache:
        auth_cache[chat_id] = set()
    auth_cache[chat_id].add(user_id)

def remove_auth_user(chat_id, user_id):
    supabase.table("auth_users").delete().eq("chat_id", chat_id).eq("user_id", user_id).execute()
    if chat_id in auth_cache and user_id in auth_cache[chat_id]:
        auth_cache[chat_id].remove(user_id)

def is_user_auth(chat_id, user_id):
    return chat_id in auth_cache and user_id in auth_cache[chat_id]
