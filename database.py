import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Auth users ko memory mein save karne ke liye set
auth_users_cache = set()

def load_auth_users():
    """Bot start hote hi database se users load karega"""
    response = supabase.table("auth_users").select("user_id").execute()
    for row in response.data:
        auth_users_cache.add(row["user_id"])

def add_auth_user(user_id):
    supabase.table("auth_users").insert({"user_id": user_id}).execute()
    auth_users_cache.add(user_id)

def remove_auth_user(user_id):
    supabase.table("auth_users").delete().eq("user_id", user_id).execute()
    if user_id in auth_users_cache:
        auth_users_cache.remove(user_id)

def is_user_auth(user_id):
    return user_id in auth_users_cache
